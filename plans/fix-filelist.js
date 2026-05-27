const fs = require('fs');
const path = 'd:\\www\\法律大模型\\plans\\法律案件追踪系统_前端重设计_v3.0.md';
let c = fs.readFileSync(path, 'utf-8');
c = c.replace(/\r\n/g, '\n');

// Fix the entire file list section
const oldSection = '## 六、文件清单\n需创建的核心文件（约 200 个）：';
const newSection = `## 六、文件清单
需创建的核心文件（约 200 个）：

- **配置文件 (7):** \`package.json\`, \`vite.config.ts\`, \`tailwind.config.ts\`, \`tsconfig.json\`, \`tsconfig.node.json\`, \`postcss.config.js\`, \`.env.example\`
- **类型定义 (22):** \`src/types/*.ts\`
- **API 客户端 (19):** \`src/api/*.ts\`
- **Zustand Store (7):** \`src/stores/*.ts\`
- **自定义 Hooks (21):** \`src/hooks/*.ts\`
- **工具函数 (7):** \`src/lib/*.ts\` + \`src/lib/export/*\`
- **UI 组件 (35+):** \`src/components/ui/*\`
- **业务组件 (70+):** \`src/components/common/*\` + \`src/components/*/*\`
- **页面 (24):** \`src/pages/*/index.tsx\`
- **样式 (3):** \`src/styles/globals.css\`, \`src/styles/print.css\`, \`src/styles/dark-mode.css\`
- **入口 (2):** \`src/App.tsx\`, \`src/main.tsx\``;

// Find the start of section 6
const startIdx = c.indexOf('## 六、文件清单');
// Find the start of section 7
const endIdx = c.indexOf('\n\n## 七、与现有后端系统的兼容性说明');

if (startIdx !== -1 && endIdx !== -1) {
  c = c.substring(0, startIdx) + newSection + c.substring(endIdx);
}

// Clean up extra blank lines
c = c.replace(/\n{4,}/g, '\n\n\n');

fs.writeFileSync(path, c, 'utf-8');
console.log('File list section completely replaced!');
