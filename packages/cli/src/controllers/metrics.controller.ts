import { Get, RestController } from '@n8n/decorators';
import type { Request } from 'express';
import { fetchMetrics } from '@/metrics/metrics.service';

@RestController('/metrics')
export class MetricsController {
	@Get('/')
	async get(req: Request) {
		const from = req.query.from as string | undefined;
		const to = req.query.to as string | undefined;
		return await fetchMetrics(from, to);
	}
}
