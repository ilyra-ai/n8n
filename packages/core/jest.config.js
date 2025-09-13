/** @type {import('jest').Config} */
const base = require('../../jest.config');

module.exports = {
	...base,
	globalSetup: '<rootDir>/test/setup.ts',
	setupFilesAfterEnv: ['<rootDir>/test/setup-mocks.ts'],
	moduleNameMapper: {
		...base.moduleNameMapper,
		'^@utils/(.*)$': '<rootDir>/../nodes-base/dist/utils/$1',
	},
};
