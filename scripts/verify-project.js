#!/usr/bin/env node

/**
 * 法律案件追踪系统 - 项目完整性检查脚本
 * 
 * 用途：验证项目代码是否符合设计文档要求
 * 运行：node scripts/verify-project.js
 */

const fs = require('fs');
const path = require('path');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

const checkResults = {
  passed: [],
  warnings: [],
  errors: [],
};

function log(type, message) {
  const prefix = {
    pass: `${colors.green}✓${colors.reset}`,
    warn: `${colors.yellow}⚠${colors.reset}`,
    error: `${colors.red}✗${colors.reset}`,
    info: `${colors.blue}ℹ${colors.reset}`,
  };
  console.log(`  ${prefix[type]} ${message}`);
}

function checkFile(filePath, description) {
  const fullPath = path.join(process.cwd(), filePath);
  if (fs.existsSync(fullPath)) {
    log('pass', `${description}: ${filePath}`);
    checkResults.passed.push(filePath);
    return true;
  } else {
    log('error', `${description}: ${filePath} (缺失)`);
    checkResults.errors.push(filePath);
    return false;
  }
}

function checkDir(dirPath, description) {
  const fullPath = path.join(process.cwd(), dirPath);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    log('pass', `${description}: ${dirPath}/`);
    checkResults.passed.push(dirPath);
    return true;
  } else {
    log('error', `${description}: ${dirPath}/ (缺失)`);
    checkResults.errors.push(dirPath);
    return false;
  }
}

function checkNoAny(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  if (!fs.existsSync(fullPath)) return;
  
  const content = fs.readFileSync(fullPath, 'utf-8');
  const anyMatches = content.match(/:\s*any\b/g);
  if (anyMatches && anyMatches.length > 0) {
    log('warn', `${filePath}: 发现 ${anyMatches.length} 处 any 类型`);
    checkResults.warnings.push(`${filePath}: ${anyMatches.length} 处 any`);
  }
}

function checkInlineStyle(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  if (!fs.existsSync(fullPath)) return;
  
  const content = fs.readFileSync(fullPath, 'utf-8');
  const styleMatches = content.match(/style=\{/g);
  if (styleMatches && styleMatches.length > 0) {
    log('warn', `${filePath}: 发现 ${styleMatches.length} 处内联样式`);
    checkResults.warnings.push(`${filePath}: ${styleMatches.length} 处内联样式`);
  }
}

// ============================================
// 开始检查
// ============================================

console.log(`\n${colors.cyan}========================================`);
console.log('法律案件追踪系统 - 项目完整性检查');
console.log('========================================\n');

// 1. 检查项目根文件
console.log(`${colors.blue}[1/8] 检查项目根文件...${colors.reset}`);
checkFile('package.json', 'package.json');
checkFile('vite.config.ts', 'Vite 配置');
checkFile('tailwind.config.ts', 'Tailwind 配置');
checkFile('tsconfig.json', 'TypeScript 配置');
checkFile('.eslintrc.cjs', 'ESLint 配置');
checkFile('.prettierrc', 'Prettier 配置');
checkFile('.env.example', '环境变量模板');

// 2. 检查目录结构
console.log(`\n${colors.blue}[2/8] 检查目录结构...${colors.reset}`);
checkDir('src', '源代码目录');
checkDir('src/api', 'API 客户端目录');
checkDir('src/components', '组件目录');
checkDir('src/components/ui', 'UI 组件目录');
checkDir('src/components/common', '通用组件目录');
checkDir('src/hooks', '自定义 Hooks 目录');
checkDir('src/stores', '状态管理目录');
checkDir('src/types', '类型定义目录');
checkDir('src/pages', '页面目录');
checkDir('src/lib', '工具函数目录');
checkDir('src/styles', '样式目录');

// 3. 检查 UI 组件
console.log(`\n${colors.blue}[3/8] 检查 UI 组件...${colors.reset}`);
checkFile('src/components/ui/button.tsx', 'Button 组件');
checkFile('src/components/ui/input.tsx', 'Input 组件');
checkFile('src/components/ui/card.tsx', 'Card 组件');
checkFile('src/components/ui/badge.tsx', 'Badge 组件');
checkFile('src/components/ui/dialog.tsx', 'Dialog 组件');
checkFile('src/components/ui/table.tsx', 'Table 组件');
checkFile('src/components/ui/skeleton.tsx', 'Skeleton 组件');
checkFile('src/components/ui/status-badge.tsx', 'StatusBadge 组件');
checkFile('src/components/ui/urgency-badge.tsx', 'UrgencyBadge 组件');

// 4. 检查通用组件
console.log(`\n${colors.blue}[4/8] 检查通用组件...${colors.reset}`);
checkFile('src/components/common/empty-state.tsx', 'EmptyState 组件');
checkFile('src/components/common/confirm-dialog.tsx', 'ConfirmDialog 组件');
checkFile('src/components/common/case-card.tsx', 'CaseCard 组件');

// 5. 检查页面
console.log(`\n${colors.blue}[5/8] 检查页面...${colors.reset}`);
checkFile('src/pages/dashboard/index.tsx', '工作台页面');
checkFile('src/pages/cases/index.tsx', '案件列表页面');

// 6. 检查 API 和类型
console.log(`\n${colors.blue}[6/8] 检查 API 和类型...${colors.reset}`);
checkFile('src/api/client.ts', 'Axios 实例');
checkFile('src/api/case.api.ts', '案件 API');
checkFile('src/types/case.types.ts', '案件类型');

// 7. 检查入口文件
console.log(`\n${colors.blue}[7/8] 检查入口文件...${colors.reset}`);
checkFile('src/main.tsx', '应用入口');
checkFile('src/App.tsx', '根组件');
checkFile('src/styles/globals.css', '全局样式');

// 8. 代码质量检查
console.log(`\n${colors.blue}[8/8] 代码质量检查...${colors.reset}`);

// 检查所有 tsx/ts 文件
const srcDir = path.join(process.cwd(), 'src');
if (fs.existsSync(srcDir)) {
  function walkDir(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory()) {
        walkDir(fullPath);
      } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
        checkNoAny(fullPath.replace(process.cwd() + path.sep, ''));
        checkInlineStyle(fullPath.replace(process.cwd() + path.sep, ''));
      }
    }
  }
  walkDir(srcDir);
}

// 检查 package.json 依赖
console.log(`\n${colors.blue}[依赖检查]${colors.reset}`);
try {
  const pkg = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'package.json'), 'utf-8'));
  const requiredDeps = [
    'react', 'react-dom', 'typescript', 'vite',
    'tailwindcss', 'axios', 'zustand', '@tanstack/react-query',
    'react-router-dom', 'lucide-react', 'react-hook-form', 'zod'
  ];
  
  const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
  for (const dep of requiredDeps) {
    if (allDeps[dep]) {
      log('pass', `${dep}: ${allDeps[dep]}`);
    } else {
      log('warn', `${dep}: 未安装`);
      checkResults.warnings.push(`缺少依赖: ${dep}`);
    }
  }
} catch (e) {
  log('error', '无法读取 package.json');
}

// ============================================
// 输出总结
// ============================================

console.log(`\n${colors.cyan}========================================`);
console.log('检查总结');
console.log('========================================\n');

console.log(`${colors.green}通过: ${checkResults.passed.length}${colors.reset}`);
console.log(`${colors.yellow}警告: ${checkResults.warnings.length}${colors.reset}`);
console.log(`${colors.red}错误: ${checkResults.errors.length}${colors.reset}`);

if (checkResults.errors.length > 0) {
  console.log(`\n${colors.red}错误列表:${colors.reset}`);
  checkResults.errors.forEach(e => console.log(`  - ${e}`));
}

if (checkResults.warnings.length > 0) {
  console.log(`\n${colors.yellow}警告列表:${colors.reset}`);
  checkResults.warnings.forEach(w => console.log(`  - ${w}`));
}

if (checkResults.errors.length === 0) {
  console.log(`\n${colors.green}🎉 项目结构完整！可以开始开发。${colors.reset}`);
} else {
  console.log(`\n${colors.red}⚠️  发现 ${checkResults.errors.length} 个错误，请修复后重试。${colors.reset}`);
}

console.log(`\n${colors.cyan}========================================\n`);

// 退出码
process.exit(checkResults.errors.length > 0 ? 1 : 0);
