<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from '@n8n/i18n';
import { useRootStore } from '@n8n/stores/useRootStore';
import { useCommunityNodesStore } from '@/stores/communityNodes.store';
import { getPlugins } from '@n8n/rest-api-client/api/plugins';

const plugins = ref([] as Array<{ name: string; official?: boolean }>);
const search = ref('');
const filter = ref('all');
const i18n = useI18n();
const rootStore = useRootStore();
const communityNodesStore = useCommunityNodesStore();

const filtered = computed(() => {
	return plugins.value.filter((p) => {
		const s = search.value.toLowerCase();
		const match = p.name.toLowerCase().includes(s);
		const f = filter.value;
		const typeMatch = f === 'all' ? true : f === 'official' ? p.official : !p.official;
		return match && typeMatch;
	});
});

async function load() {
	const list = await getPlugins(rootStore.restApiContext);
	plugins.value = list;
}

async function install(name: string) {
	await communityNodesStore.installPackage(name);
}

onMounted(load);
</script>

<template>
	<div>
		<div>
			<input v-model="search" :placeholder="i18n.baseText('plugins.search')" />
			<select v-model="filter">
				<option value="all">{{ i18n.baseText('plugins.filter.all') }}</option>
				<option value="official">{{ i18n.baseText('plugins.filter.official') }}</option>
				<option value="community">{{ i18n.baseText('plugins.filter.community') }}</option>
			</select>
		</div>
		<ul>
			<li v-for="plugin in filtered" :key="plugin.name">
				<span>{{ plugin.name }}</span>
				<button @click="install(plugin.name)">{{ i18n.baseText('plugins.install') }}</button>
			</li>
		</ul>
	</div>
</template>
