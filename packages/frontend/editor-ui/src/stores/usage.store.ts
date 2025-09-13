import { computed, reactive } from 'vue';
import { defineStore } from 'pinia';
import type { UsageState } from '@/Interface';
import * as usageApi from '@/api/usage';
import { useRootStore } from '@n8n/stores/useRootStore';
import { useSettingsStore } from '@/stores/settings.store';

export type UsageTelemetry = {
	instance_id: string;
	action: 'view_plans' | 'manage_plan' | 'add_activation_key' | 'desktop_view_plans';
	plan_name_current: string;
	usage: number;
	quota: number;
};

const DEFAULT_PLAN_NAME = 'Community';
const DEFAULT_STATE: UsageState = {
	loading: true,
	plansEnabled: true,
	data: {
		usage: {
			activeWorkflowTriggers: {
				limit: -1,
				value: 0,
				warningThreshold: 0.8,
			},
			workflowsHavingEvaluations: {
				value: 0,
				limit: 0,
			},
		},
		license: {
			planId: '',
			planName: DEFAULT_PLAN_NAME,
		},
	},
};

export const useUsageStore = defineStore('usage', () => {
	const rootStore = useRootStore();
	const settingsStore = useSettingsStore();

	const state = reactive<UsageState>({ ...DEFAULT_STATE });

	const plansEnabled = computed(() => state.plansEnabled);
	const planName = computed(() => state.data.license.planName || DEFAULT_PLAN_NAME);
	const planId = computed(() => state.data.license.planId);
	const activeWorkflowTriggersLimit = computed(() =>
		state.plansEnabled ? state.data.usage.activeWorkflowTriggers.limit : -1,
	);
	const activeWorkflowTriggersCount = computed(() => state.data.usage.activeWorkflowTriggers.value);
	const workflowsWithEvaluationsLimit = computed(() =>
		state.plansEnabled ? state.data.usage.workflowsHavingEvaluations.limit : -1,
	);
	const workflowsWithEvaluationsCount = computed(
		() => state.data.usage.workflowsHavingEvaluations.value,
	);
	const executionPercentage = computed(() =>
		activeWorkflowTriggersLimit.value > 0
			? (activeWorkflowTriggersCount.value / activeWorkflowTriggersLimit.value) * 100
			: 0,
	);
	const instanceId = computed(() => settingsStore.settings.instanceId);
	const managementToken = computed(() => state.data.managementToken);
	const appVersion = computed(() => settingsStore.settings.versionCli);
	const commonSubscriptionAppUrlQueryParams = computed(
		() => `instanceid=${instanceId.value}&version=${appVersion.value}`,
	);
	const subscriptionAppUrl = computed(() =>
		settingsStore.settings.license.environment === 'production'
			? 'https://subscription.n8n.io'
			: 'https://staging-subscription.n8n.io',
	);

	const setLoading = (loading: boolean) => {
		state.loading = loading;
	};

	const setData = (data: UsageState['data']) => {
		state.data = data;
	};

	const setPlansEnabled = (value: boolean) => {
		state.plansEnabled = value;
	};

	const getLicenseInfo = async () => {
		const data = await usageApi.getLicense(rootStore.restApiContext);
		setData(data);
	};

	const activateLicense = async (activationKey: string) => {
		const data = await usageApi.activateLicenseKey(rootStore.restApiContext, { activationKey });
		setData(data);
		await settingsStore.getSettings();
		await settingsStore.getModuleSettings();
	};

	const refreshLicenseManagementToken = async () => {
		try {
			const data = await usageApi.renewLicense(rootStore.restApiContext);
			setData(data);
		} catch (error) {
			await getLicenseInfo();
		}
	};

	const requestEnterpriseLicenseTrial = async () => {
		await usageApi.requestLicenseTrial(rootStore.restApiContext);
	};

	const registerCommunityEdition = async (email: string) =>
		await usageApi.registerCommunityEdition(rootStore.restApiContext, { email });

	return {
		setLoading,
		getLicenseInfo,
		setData,
		setPlansEnabled,
		activateLicense,
		refreshLicenseManagementToken,
		requestEnterpriseLicenseTrial,
		registerCommunityEdition,
		plansEnabled,
		planName,
		planId,
		activeWorkflowTriggersLimit,
		activeWorkflowTriggersCount,
		workflowsWithEvaluationsLimit,
		workflowsWithEvaluationsCount,
		executionPercentage,
		instanceId,
		managementToken,
		appVersion,
		isCloseToLimit: computed(() =>
			state.data.usage.activeWorkflowTriggers.limit < 0
				? false
				: activeWorkflowTriggersCount.value / activeWorkflowTriggersLimit.value >=
					state.data.usage.activeWorkflowTriggers.warningThreshold,
		),
		viewPlansUrl: computed(
			() => `${subscriptionAppUrl.value}?${commonSubscriptionAppUrlQueryParams.value}`,
		),
		managePlanUrl: computed(
			() =>
				`${subscriptionAppUrl.value}/manage?token=${managementToken.value}&${commonSubscriptionAppUrlQueryParams.value}`,
		),
		isLoading: computed(() => state.loading),
		telemetryPayload: computed<UsageTelemetry>(() => ({
			instance_id: instanceId.value,
			action: 'view_plans',
			plan_name_current: planName.value,
			usage: activeWorkflowTriggersCount.value,
			quota: activeWorkflowTriggersLimit.value,
		})),
	};
});
