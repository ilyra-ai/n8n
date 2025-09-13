<template>
	<div>
		<select v-model="workflow">
			<option value="">All</option>
			<option v-for="id in workflows" :key="id" :value="id">{{ id }}</option>
		</select>
		<Chart :data="latency" />
		<Chart :data="throughput" />
		<Chart :data="errors" />
	</div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Chart } from 'vue-chartjs';
import type { ChartData } from 'chart.js';
import { useApi } from '@/composables/useApi';

const api = useApi();
const workflow = ref('');
const workflows = ref<string[]>([]);
const latency = ref<ChartData<'line'>>({ labels: [], datasets: [{ label: 'latency', data: [] }] });
const throughput = ref<ChartData<'line'>>({
	labels: [],
	datasets: [{ label: 'throughput', data: [] }],
});
const errors = ref<ChartData<'bar'>>({ labels: [], datasets: [{ label: 'errors', data: [] }] });

async function load() {
	const data = await api.get('/metrics');
	const filtered = workflow.value
		? data.filter((m: any) => m.workflow_id === workflow.value)
		: data;
	workflows.value = [...new Set(data.map((m: any) => m.workflow_id).filter(Boolean))];
	latency.value = {
		labels: filtered.filter((m: any) => m.type === 'latency').map((m: any) => m.created_at),
		datasets: [
			{
				label: 'latency',
				data: filtered.filter((m: any) => m.type === 'latency').map((m: any) => m.value),
			},
		],
	};
	throughput.value = {
		labels: filtered.filter((m: any) => m.type === 'throughput').map((m: any) => m.created_at),
		datasets: [
			{
				label: 'throughput',
				data: filtered.filter((m: any) => m.type === 'throughput').map((m: any) => m.value),
			},
		],
	};
	errors.value = {
		labels: filtered.filter((m: any) => m.type === 'error').map((m: any) => m.created_at),
		datasets: [
			{ label: 'errors', data: filtered.filter((m: any) => m.type === 'error').map(() => 1) },
		],
	};
}

onMounted(load);
watch(workflow, load);
</script>
