import axios from 'axios';
import { Service } from '@n8n/di';

@Service()
export class PluginsService {
	async getRegistry() {
		const url = 'https://raw.githubusercontent.com/n8n-io/plugins/main/registry.json';
		const { data } = await axios.get(url);
		return data;
	}
}
