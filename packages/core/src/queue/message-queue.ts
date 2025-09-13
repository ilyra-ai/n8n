import { Queue, QueueScheduler, JobsOptions } from 'bullmq';
import type { RedisOptions } from 'ioredis';

export class MessageQueue<T> {
	queue: Queue<T>;
	scheduler: QueueScheduler;
	connection: RedisOptions;
	constructor(name: string, connection: RedisOptions) {
		this.queue = new Queue<T>(name, { connection });
		this.scheduler = new QueueScheduler(name, { connection });
		this.connection = connection;
	}
	add(name: string, data: T, opts?: JobsOptions) {
		return this.queue.add(name, data, {
			attempts: 3,
			backoff: { type: 'exponential', delay: 5000 },
			removeOnComplete: true,
			...opts,
		});
	}
}
