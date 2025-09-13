import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.METRICS_DB });

export async function fetchMetrics(from?: string, to?: string) {
	if (from && to)
		return (
			await pool.query(
				'select * from execution_metrics where created_at between $1 and $2 order by created_at',
				[from, to],
			)
		).rows;
	return (await pool.query('select * from execution_metrics order by created_at desc limit 100'))
		.rows;
}
