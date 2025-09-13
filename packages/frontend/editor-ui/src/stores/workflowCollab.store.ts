import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useRootStore } from '@n8n/stores/useRootStore';
import { useWorkflowsStore } from './workflows.store';
import { useUsersStore } from './users.store';
import { useWebSocketClient } from '@/push-connection/useWebSocketClient';

export const useWorkflowCollabStore = defineStore('workflowCollab', () => {
	const rootStore = useRootStore();
	const workflowsStore = useWorkflowsStore();
	const usersStore = useUsersStore();
	const cursors = ref<Record<string, unknown>>({});
	let client: ReturnType<typeof useWebSocketClient> | null = null;
	function wsUrl() {
		const rest = rootStore.restUrl;
		const { protocol, host } = window.location;
		const base = rest.startsWith('http')
			? rest.replace(/^http/, 'ws')
			: `${protocol === 'https:' ? 'wss' : 'ws'}://${host + rest}`;
		return `${base}/workflow`;
	}
	function onMessage(data: unknown) {
		let msg;
		try {
			msg = JSON.parse(data as string);
		} catch {
			return;
		}
		if (msg.type === 'update' && msg.workflowId === workflowsStore.workflowId) {
			workflowsStore.setWorkflow(msg.workflow);
		}
		if (msg.type === 'cursor' && msg.workflowId === workflowsStore.workflowId) {
			cursors.value[msg.userId] = msg.cursor;
		}
	}
	function connect() {
		client = useWebSocketClient({ url: wsUrl(), onMessage });
		client.connect();
		client.sendMessage(
			JSON.stringify({
				type: 'join',
				workflowId: workflowsStore.workflowId,
				userId: usersStore.currentUserId,
			}),
		);
	}
	function disconnect() {
		client?.disconnect();
		client = null;
	}
	function sendUpdate(workflow: object) {
		client?.sendMessage(
			JSON.stringify({
				type: 'update',
				workflowId: workflowsStore.workflowId,
				userId: usersStore.currentUserId,
				workflow,
			}),
		);
	}
	function sendCursor(cursor: unknown) {
		client?.sendMessage(
			JSON.stringify({
				type: 'cursor',
				workflowId: workflowsStore.workflowId,
				userId: usersStore.currentUserId,
				cursor,
			}),
		);
	}
	return { cursors, connect, disconnect, sendUpdate, sendCursor };
});
