import js from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["dist/", "node_modules/"] },

  js.configs.recommended,

  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser },
    },
    rules: {
      "no-unused-vars": "warn",
      eqeqeq: "error",
      "no-console": "warn",
    },
  },

  {
    files: ["*.config.js"],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
];