#!/usr/bin/env node

/**
 * 法律案件追踪系统 - 深度完整性检查脚本
 * 
 * 运行方式：
 *   方式1: 在项目根目录运行: node scripts/deep-verify-project.js
 *   方式2: 在 frontend 目录运行: node ../scripts/deep-verify-project.js
 */

const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

const results = {
  passed: [],
  warnings: [],
  errors: [],
  emptyFiles: [],
};

// 自动检测项目根目录
function findProjectRoot() {
  let dir = process.cwd();
  // 如果当前目录有 frontend/src，说明在根目录
  if (fs.existsSync(path.join(dir, 'frontend', 'src'))) {
    return path.join(dir, 'frontend');
  }
  // 如果当前目录有 src，说明在 frontend 目录
  if (fs.existsSync(path.join(dir, 'src'))) {
    return dir;
  }
  // 如果当前目录有 package.json 且包含 react
  if (fs.existsSync(path.join(dir, 'package.json'))) {
    try {
      const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf-8'));
      if (pkg.dependencies && pkg.dependencies.react) {
        return dir;
      }
    } catch {}
  }
  return null;
}

const FRONTEND_DIR = findProjectRoot();

if (!FRONTEND_DIR) {
  console.log(`${colors.red}错误: 无法找到项目目录。请在项目根目录或 frontend 目录下运行此脚本。${colors.reset}`);
  process.exit(1);
}

console.log(`${colors.cyan}项目目录: ${FRONTEND_DIR}${colors.reset}\n`);

function log(type, message) {
  const prefix = {
    pass: `${colors.green}✓${colors.reset}`,
    warn: `${colors.yellow}⚠${colors.reset}`,
    error: `${colors.red}✗${colors.reset}`,
    empty: `${colors.red}◌${colors.reset}`,
  };
  console.log(`  ${prefix[type]} ${message}`);
}

function checkFile(filePath, description) {
  const fullPath = path.join(FRONTEND_DIR, filePath);
  
  if (!fs.existsSync(fullPath)) {
    log('error', `${description}: ${filePath} (文件不存在)`);
    results.errors.push(filePath);
    return false;
  }
  
  const stat = fs.statSync(fullPath);
  
  if (stat.size === 0) {
    log('empty', `${description}: ${filePath} (文件为空！)`);
    results.emptyFiles.push(filePath);
    results.errors.push(filePath);
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf-8');
  
  const codeContent = content
    .replace(/\/\/.*$/gm, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\s/g, '');
  
  if (codeContent.length < 10) {
    log('empty', `${description}: ${filePath} (几乎为空，${stat.size} 字节)`);
    results.emptyFiles.push(filePath);
    results.errors.push(filePath);
    return false;
  }
  
  const anyMatches = content.match(/:\s*any\b/g);
  if (anyMatches && anyMatches.length > 0) {
    log('warn', `${filePath}: ${anyMatches.length} 处 any 类型`);
    results.warnings.push(`${filePath}: ${anyMatches.length} 处 any`);
  }
  
  const styleMatches = content.match(/style=\{/g);
  if (styleMatches && styleMatches.length > 0) {
    log('warn', `${filePath}: ${styleMatches.length} 处内联样式`);
    results.warnings.push(`${filePath}: ${styleMatches.length} 处内联样式`);
  }
  
  if ((filePath.endsWith('.tsx') || filePath.endsWith('.ts')) && !filePath.includes('.stories.')) {
    const hasExport = /export\s+(default\s+)?(function|class|const|interface|type|enum)/.test(content);
    if (!hasExport) {
      log('warn', `${filePath}: 无 export`);
      results.warnings.push(`${filePath}: 无 export`);
    }
  }
  
  log('pass', `${description}: ${filePath} (${stat.size} bytes)`);
  results.passed.push(filePath);
  return true;
}

function checkDir(dirPath, description) {
  const fullPath = path.join(FRONTEND_DIR, dirPath);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    const files = fs.readdirSync(fullPath);
    log('pass', `${description}: ${dirPath}/ (${files.length} 个文件)`);
    results.passed.push(dirPath);
    return true;
  } else {
    log('error', `${description}: ${dirPath}/ (目录不存在)`);
    results.errors.push(dirPath);
    return false;
  }
}

// ============================================
// 开始检查
// ============================================

console.log(`\n${colors.cyan}${colors.bold}========================================`);
console.log('法律案件追踪系统 - 深度完整性检查');
console.log('========================================\n');

console.log(`${colors.blue}${colors.bold}[1/9] 检查项目根文件...${colors.reset}`);
checkFile('package.json', 'package.json');
checkFile('vite.config.ts', 'Vite 配置');
checkFile('tailwind.config.ts', 'Tailwind 配置');
checkFile('tsconfig.json', 'TypeScript 配置');
checkFile('.eslintrc.json', 'ESLint 配置');
checkFile('.prettierrc', 'Prettier 配置');
checkFile('.env.example', '环境变量模板');

console.log(`\n${colors.blue}${colors.bold}[2/9] 检查目录结构...${colors.reset}`);
checkDir('src', '源代码目录');
checkDir('src/api', 'API 客户端目录');
checkDir('src/components', '组件目录');
checkDir('src/components/ui', 'UI 组件目录');
checkDir('src/components/common', '通用组件目录');
checkDir('src/components/layout', '布局组件目录');
checkDir('src/hooks', '自定义 Hooks 目录');
checkDir('src/stores', '状态管理目录');
checkDir('src/types', '类型定义目录');
checkDir('src/pages', '页面目录');
checkDir('src/lib', '工具函数目录');
checkDir('src/styles', '样式目录');

console.log(`\n${colors.blue}${colors.bold}[3/9] 检查布局组件（关键）...${colors.reset}`);
checkFile('src/components/layout/app-shell.tsx', 'AppShell 布局');
checkFile('src/components/layout/sidebar.tsx', '侧边栏');
checkFile('src/components/layout/header.tsx', '顶部栏');

console.log(`\n${colors.blue}${colors.bold}[4/9] 检查入口文件...${colors.reset}`);
checkFile('src/main.tsx', '应用入口');
checkFile('src/App.tsx', '根组件');
checkFile('src/styles/globals.css', '全局样式');

console.log(`\n${colors.blue}${colors.bold}[5/9] 检查 API 客户端...${colors.reset}`);
checkFile('src/api/client.ts', 'Axios 实例');
checkFile('src/api/case.api.ts', '案件 API');
checkFile('src/api/dashboard.api.ts', 'Dashboard API');
checkFile('src/lib/api-config.ts', 'API 配置');

console.log(`\n${colors.blue}${colors.bold}[6/9] 检查 UI 组件...${colors.reset}`);
checkFile('src/components/ui/button.tsx', 'Button 组件');
checkFile('src/components/ui/input.tsx', 'Input 组件');
checkFile('src/components/ui/card.tsx', 'Card 组件');
checkFile('src/components/ui/status-badge.tsx', 'StatusBadge 组件');
checkFile('src/components/ui/urgency-badge.tsx', 'UrgencyBadge 组件');
checkFile('src/components/ui/skeleton.tsx', 'Skeleton 组件');

console.log(`\n${colors.blue}${colors.bold}[7/9] 检查通用组件...${colors.reset}`);
checkFile('src/components/common/empty-state.tsx', 'EmptyState 组件');
checkFile('src/components/common/confirm-dialog.tsx', 'ConfirmDialog 组件');
checkFile('src/components/common/case-card.tsx', 'CaseCard 组件');

console.log(`\n${colors.blue}${colors.bold}[8/9] 检查页面...${colors.reset}`);
checkFile('src/pages/dashboard/index.tsx', '工作台页面');
checkFile('src/pages/cases/index.tsx', '案件列表页面');

console.log(`\n${colors.blue}${colors.bold}[9/9] 项目统计...${colors.reset}`);

const srcDir = path.join(FRONTEND_DIR, 'src');
let totalFiles = 0, tsxCount = 0, tsCount = 0, cssCount = 0, emptyCount = 0;

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      walkDir(fullPath);
    } else {
      totalFiles++;
      const ext = path.extname(file);
      if (ext === '.tsx') tsxCount++;
      else if (ext === '.ts') tsCount++;
      else if (ext === '.css') cssCount++;
      
      if (stat.size === 0) {
        emptyCount++;
        results.emptyFiles.push(fullPath.replace(FRONTEND_DIR + path.sep, ''));
      }
    }
  }
}
walkDir(srcDir);

console.log(`\n  总文件数: ${totalFiles}`);
console.log(`  TSX 组件: ${tsxCount}`);
console.log(`  TS 文件: ${tsCount}`);
console.log(`  CSS 样式: ${cssCount}`);
console.log(`  空文件: ${emptyCount}`);

// ============================================
// 输出总结
// ============================================

console.log(`\n${colors.cyan}${colors.bold}========================================`);
console.log('检查总结');
console.log('========================================\n');

console.log(`${colors.green}${colors.bold}通过: ${results.passed.length}${colors.reset}`);
console.log(`${colors.yellow}${colors.bold}警告: ${results.warnings.length}${colors.reset}`);
console.log(`${colors.red}${colors.bold}错误: ${results.errors.length}${colors.reset}`);
console.log(`${colors.red}${colors.bold}空文件: ${results.emptyFiles.length}${colors.reset}`);

if (results.emptyFiles.length > 0 && results.emptyFiles.length <= 20) {
  console.log(`\n${colors.red}${colors.bold}空文件列表:${colors.reset}`);
  results.emptyFiles.forEach(f => console.log(`  ${colors.red}◌${colors.reset} ${f}`));
} else if (results.emptyFiles.length > 20) {
  console.log(`\n${colors.red}${colors.bold}空文件过多 (${results.emptyFiles.length} 个)，仅显示前 20 个:${colors.reset}`);
  results.emptyFiles.slice(0, 20).forEach(f => console.log(`  ${colors.red}◌${colors.reset} ${f}`));
}

if (results.errors.length === 0 && results.emptyFiles.length === 0) {
  console.log(`\n${colors.green}${colors.bold}🎉 项目结构完整！所有文件都有实际内容。${colors.reset}`);
} else {
  console.log(`\n${colors.red}${colors.bold}⚠️  发现 ${results.errors.length} 个错误，${results.emptyFiles.length} 个空文件。${colors.reset}`);
}

console.log(`\n${colors.cyan}${colors.bold}========================================\n`);

process.exit(results.errors.length > 0 ? 1 : 0);
