import { Get, RestController } from '@n8n/decorators';
import { PluginsService } from '@/services/plugins.service';

@RestController('/plugins')
export class PluginsController {
	constructor(private readonly pluginsService: PluginsService) {}

	@Get('/')
	async getPlugins() {
		return await this.pluginsService.getRegistry();
	}
}
