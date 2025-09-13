import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.METRICS_DB });

export function recordLatency(workflowId: string, value: number) {
	return pool.query(
		'insert into execution_metrics(workflow_id,type,value,created_at) values ($1,$2,$3,now())',
		[workflowId, 'latency', value],
	);
}

export function recordError(workflowId: string, message: string) {
	return pool.query(
		'insert into execution_metrics(workflow_id,type,message,created_at) values ($1,$2,$3,now())',
		[workflowId, 'error', message],
	);
}

export function recordThroughput(count: number) {
	return pool.query('insert into execution_metrics(type,value,created_at) values ($1,$2,now())', [
		'throughput',
		count,
	]);
}
