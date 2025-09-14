import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

export class PersistentCache<V> {
        private file: string;
        private data: Record<string, V> = {};
        constructor(file = process.env.AI_PERSISTENT_CACHE_PATH ?? join(tmpdir(), 'ai-workflow-cache.json')) {
                this.file = file;
                try {
                        this.data = JSON.parse(readFileSync(this.file, 'utf8'));
                } catch {}
        }
        get(key: string): V | undefined {
                return this.data[key];
        }
        set(key: string, value: V) {
                this.data[key] = value;
                writeFileSync(this.file, JSON.stringify(this.data));
        }
}
