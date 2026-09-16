/** @type {import('jest').Config} */
const config = {
  testEnvironment: "jsdom",
  // Runs after the test framework is installed — adds @testing-library/jest-dom matchers
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  transform: {
    "^.+\\.(ts|tsx)$": ["ts-jest", { tsconfig: { jsx: "react-jsx" } }],
  },
  testMatch: ["**/*.test.tsx", "**/*.test.ts"],
  collectCoverageFrom: ["components/**/*.tsx", "app/**/*.tsx", "lib/**/*.ts"],
};

module.exports = config;
