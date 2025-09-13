import vm from 'vm';

export class PluginSandbox {
	run(code: string, context: Record<string, unknown> = {}) {
		const sandbox = { ...context };
		vm.createContext(sandbox);
		const script = new vm.Script(code);
		return script.runInContext(sandbox);
	}
}
