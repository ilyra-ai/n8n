import type { IRestApiContext } from '../types';
import { get } from '../utils';

export async function getPlugins(context: IRestApiContext) {
	const response = await get(context.baseUrl, '/plugins');
	return response.data || [];
}
