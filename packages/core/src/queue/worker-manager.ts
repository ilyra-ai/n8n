import { Worker } from 'bullmq';
import type { MessageQueue } from './message-queue';

export class WorkerManager<T> {
	private worker?: Worker<T>;
	constructor(
		private queue: MessageQueue<T>,
		private processor: (job: any) => Promise<any>,
	) {}
	start(concurrency: number) {
		this.worker = new Worker<T>(this.queue.queue.name, this.processor, {
			connection: this.queue.connection,
			concurrency,
		});
		this.worker.on('failed', async (job) => {
			if (job.attemptsMade < (job.opts.attempts ?? 1)) await job.retry();
		});
	}
	async scale(concurrency: number) {
		if (this.worker) await this.worker.close();
		this.start(concurrency);
	}
	async stop() {
		if (this.worker) await this.worker.close();
	}
}
