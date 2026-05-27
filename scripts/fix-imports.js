const fs = require('fs');

// Fix case detail page import
const pagePath = 'd:\\www\\法律大模型\\frontend\\src\\pages\\cases\\[id]\\index.tsx';
let pageContent = fs.readFileSync(pagePath, 'utf-8');
pageContent = pageContent.replace("import { useCase } from '@/hooks/use-case';", "import { useCaseDetail } from '@/hooks/use-case';");
pageContent = pageContent.replace('useCase(id', 'useCaseDetail(id');
fs.writeFileSync(pagePath, pageContent, 'utf-8');
console.log('Fixed case detail page import');

// Fix overview page import
const overviewPath = 'd:\\www\\法律大模型\\frontend\\src\\pages\\cases\\[id]\\overview.tsx';
let overviewContent = fs.readFileSync(overviewPath, 'utf-8');
overviewContent = overviewContent.replace("import { useCase } from '@/hooks/use-case';", "import { useCaseDetail } from '@/hooks/use-case';");
overviewContent = overviewContent.replace('useCase(id', 'useCaseDetail(id');
fs.writeFileSync(overviewPath, overviewContent, 'utf-8');
console.log('Fixed overview page import');
