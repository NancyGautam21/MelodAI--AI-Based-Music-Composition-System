import os
import json
import hashlib
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple



class CacheManager:
    def __init__(self, cache_dir: str = 'cache', max_files: int = 50, max_size_mb: int = 500, ttl_hours: int = 1):
        """
        Initialize the Cache Manager.
        
        Args:
            cache_dir (str): Directory to store cached files
            max_files (int): Maximum number of files to keep in cache
            max_size_mb (int): Maximum total size of cache in MB
            ttl_hours (int): Time to live for cached items in hours
        """
        # Resolve absolute path for cache directory relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = os.path.join(base_dir, cache_dir)
        self.max_files = max_files
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_hours * 3600
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0,
            'count': 0
        }
        
        self._initialize_cache()

    def _initialize_cache(self):
        """Create cache directory if it doesn't exist and load stats"""
        os.makedirs(self.cache_dir, exist_ok=True)
        self._update_stats_from_disk()

    def _update_stats_from_disk(self):
        """Recalculate cache usage from disk"""
        total_size = 0
        count = 0
        # Iterate only files, not subdirectories
        for p in Path(self.cache_dir).glob('*'):
            if p.is_file() and not p.name.endswith('.json'): # Count audio files
                total_size += p.stat().st_size
                count += 1
        
        self.stats['size_bytes'] = total_size
        self.stats['count'] = count

    def get_cache_key(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key based on prompt and parameters"""
        # Sort params to ensure consistent ordering
        param_str = json.dumps(params, sort_keys=True)
        content = f"{prompt}|{param_str}"
        key = hashlib.md5(content.encode('utf-8')).hexdigest()
        print(f"🔑 Cache Key Gen: '{prompt[:20]}...' + {params} -> {key}")
        return key

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve item from cache if exists and not expired.
        Returns dict with 'file_path' and 'metadata' or None.
        """
        audio_filename = f"{cache_key}.mp3" # Assuming mp3 for now, logic can adapt
        meta_filename = f"{cache_key}.json"
        
        audio_path = os.path.join(self.cache_dir, audio_filename)
        meta_path = os.path.join(self.cache_dir, meta_filename)
        
        # Check existence
        if not (os.path.exists(audio_path) and os.path.exists(meta_path)):
            print(f"🛑 Cache Miss: Files not found for {cache_key}")
            self.stats['misses'] += 1
            return None
            
        # Check TTL
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = metadata.get('timestamp', 0)
            if time.time() - cached_time > self.ttl_seconds:
                # Expired
                self._remove_item(cache_key)
                self.stats['misses'] += 1
                return None
                
            # Update access time (touch the file) for LRU
            Path(audio_path).touch()
            
            self.stats['hits'] += 1
            return {
                'file_path': audio_path,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"⚠️ Error reading cache: {e}")
            self.stats['misses'] += 1
            return None

    def set(self, cache_key: str, audio_file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Add item to cache. Handles eviction if needed.
        """
        try:
            # Prepare paths
            ext = os.path.splitext(audio_file_path)[1]
            if not ext: ext = '.mp3'
            
            target_audio_name = f"{cache_key}{ext}"
            target_audio_path = os.path.join(self.cache_dir, target_audio_name)
            target_meta_path = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # Check limits before adding
            file_size = os.path.getsize(audio_file_path)
            self._enforce_limits(new_file_size=file_size)
            
            # Copy audio file
            shutil.copy2(audio_file_path, target_audio_path)
            # Ensure timestamp is current (copy2 preserves source timestamp)
            Path(target_audio_path).touch()
            
            # Add timestamp to metadata
            metadata['timestamp'] = time.time()
            metadata['cache_key'] = cache_key
            
            # Write metadata
            with open(target_meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            self._update_stats_from_disk()
            return True
            
        except Exception as e:
            print(f"❌ Error setting cache: {e}")
            return False

    def _enforce_limits(self, new_file_size: int = 0):
        """Evict least recently used items if limits are exceeded"""
        # Get all cached items with their access times
        items = []
        for p in Path(self.cache_dir).glob('*.json'):
            try:
                audio_path = p.with_suffix('.mp3') # Assumption
                if not audio_path.exists():
                    # Try to find the audio file if extension differs? 
                    # For simplicty assume mp3 matching json stem
                    continue
                    
                access_time = audio_path.stat().st_mtime
                items.append({
                    'key': p.stem,
                    'path': str(audio_path),
                    'meta_path': str(p),
                    'size': audio_path.stat().st_size,
                    'atime': access_time
                })
            except Exception:
                continue
                
        # Sort by access time (oldest first)
        items.sort(key=lambda x: x['atime'])
        
        current_size = self.stats['size_bytes']
        current_count = self.stats['count']
        
        # Evict while limits exceeded
        # Simulating adding the new file
        while (current_count + 1 > self.max_files) or \
              (current_size + new_file_size > self.max_size_bytes):
            
            if not items:
                break
                
            victim = items.pop(0)
            self._remove_item(victim['key'])
            
            current_size -= victim['size']
            current_count -= 1
            self.stats['evictions'] += 1
            print(f" Evicted cache item: {victim['key']} (LRU)")

    def _remove_item(self, cache_key: str):
        """Remove audio and metadata for a key"""
        for ext in ['.mp3', '.wav', '.json']:
            p = os.path.join(self.cache_dir, f"{cache_key}{ext}")
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        self._update_stats_from_disk()

    def clear(self):
        """Clear entire cache"""
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir)
        self._initialize_cache()
        print("🧹 Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Return current statistics"""
        return {
            **self.stats,
            'max_files': self.max_files,
            'max_size_mb': self.max_size_bytes / (1024*1024)
        }

if __name__ == "__main__":
    print("🧪 === Testing Cache Manager Implementation ===\n")
    
    # 1. Setup Test Environment
    print("1️⃣  Initializing Cache Manager (Limit: 3 files)...")
    # Using a temporary test directory specifically for the run
    # To avoid messing with real cache if it exists, but for this task we can use a test subdir
    cm = CacheManager(cache_dir='test_cache_demo', max_files=3, max_size_mb=10, ttl_hours=1)
    cm.clear()
    
    # Create a dummy audio file
    dummy_audio = "test_audio.mp3"
    with open(dummy_audio, 'w') as f:
        f.write("fake audio content " * 100)
    
    try:
        # 2. Test Set & Get
        print("\n2️⃣  Testing Cache SET and GET...")
        
        # Case A: Cache Miss & Set
        print("   🔹 Requesting 'Summer Vibes' (First time)...")
        prompt = "Summer Vibes"
        params = {"duration": 30, "temp": 1.0}
        key = cm.get_cache_key(prompt, params)
        
        result = cm.get(key)
        if result is None:
            print("   ❌ Cache Miss (Expected)")
            print("   💾 Caching result...")
            cm.set(key, dummy_audio, {"prompt": prompt, "params": params})
        
        # Case B: Cache Hit
        print("\n   🔹 Requesting 'Summer Vibes' (Second time)...")
        result = cm.get(key)
        if result:
            print("   ✅ Cache HIT!")
            print(f"   📂 Retrieved from: {os.path.basename(result['file_path'])}")
        
        # 3. Test LRU Eviction
        print("\n3️ Testing LRU Eviction (Max 3 files)...")
        
        prompts = ["Lo-fi Study", "Heavy Metal", "Classical Piano"]
        for p in prompts:
            print(f"   ➕ Caching: {p}")
            k = cm.get_cache_key(p, params)
            cm.set(k, dummy_audio, {"prompt": p})
            time.sleep(0.1) # Ensure different timestamps
            
        print("\n   Current Stats:")
        stats = cm.get_stats()
        print(f"   Files in cache: {stats['count']}")
        print(f"   Evictions: {stats['evictions']}")
        
        # Verify 'Summer Vibes' was evicted (it was the oldest)
        key_summer = cm.get_cache_key("Summer Vibes", params)
        if cm.get(key_summer) is None:
            print("   ✅ 'Summer Vibes' was correctly evicted (LRU working)")
        else:
            print("   ❌ 'Summer Vibes' still in cache (LRU failed)")

        # 4. Final Stats
        print("\n4️⃣  Final Cache Statistics")
        print("=" * 40)
        final_stats = cm.get_stats()
        print(f"   Total Hits:      {final_stats['hits']}")
        print(f"   Total Misses:    {final_stats['misses']}")
        print(f"   Total Evictions: {final_stats['evictions']}")
        print(f"   Storage Used:    {final_stats['size_bytes']} bytes")
        print(f"   File Count:      {final_stats['count']} / {final_stats['max_files']}")
        print("=" * 40)
        
    finally:
        # Cleanup
        if os.path.exists(dummy_audio):
            os.remove(dummy_audio)
        # Optional: cleanup test dir
        # shutil.rmtree(cm.cache_dir) 
        pass