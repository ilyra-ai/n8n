import type { Server as HttpServer } from 'http';
import WebSocket, { WebSocketServer } from 'ws';

type Client = WebSocket & { workflowId?: string };

export class WorkflowWsService {
	private wss?: WebSocketServer;
	private channels = new Map<string, Set<Client>>();

	start(server: HttpServer) {
		this.wss = new WebSocketServer({ server });
		this.wss.on('connection', (ws: Client) => {
			ws.on('message', (msg) => {
				let data;
				try {
					data = JSON.parse(msg.toString());
				} catch {
					return;
				}
				if (data.type === 'join') {
					ws.workflowId = data.workflowId;
					const set = this.channels.get(data.workflowId) ?? new Set();
					set.add(ws);
					this.channels.set(data.workflowId, set);
					return;
				}
				if (data.workflowId) {
					const set = this.channels.get(data.workflowId);
					if (!set) return;
					for (const client of set) {
						if (client !== ws && client.readyState === WebSocket.OPEN) {
							client.send(msg.toString());
						}
					}
				}
			});
			ws.on('close', () => {
				const id = ws.workflowId;
				if (!id) return;
				const set = this.channels.get(id);
				if (!set) return;
				set.delete(ws);
				if (!set.size) this.channels.delete(id);
			});
		});
	}
}
