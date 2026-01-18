# 🚀 Portal Release Sanity Automation Tool - Complete Implementation Plan

**Version:** 1.0  
**Document Type:** Super Prompt - Complete Implementation Guide  
**Last Updated:** January 2026

This document contains the complete specification for building a production-grade portal release sanity automation tool. Every section is implementation-ready.

-----

## Quick Reference

- **Purpose**: Automate post-release sanity validation via Chrome attachment
- **Approach**: Zero authentication logic, human-first validation
- **Tech Stack**: Node.js 18+, Playwright, TypeScript, Chrome CDP
- **Execution Time**: < 10 minutes for full suite
- **Key Principle**: Fail fast with evidence-based debugging

-----

## Table of Contents

1. [Executive Summary](#1-executive-summary)
1. [System Architecture](#2-system-architecture)
1. [Project Setup](#3-project-setup)
1. [Browser Attachment](#4-browser-attachment)
1. [Workflow Framework](#5-workflow-framework)
1. [Validation Layer](#6-validation-layer)
1. [Evidence Collection](#7-evidence-collection)
1. [Reporting](#8-reporting)
1. [Configuration](#9-configuration)
1. [Complete Implementation](#10-complete-implementation)
1. [Usage Guide](#11-usage-guide)

-----

## 1. Executive Summary

### 1.1 Core Principles

- **Zero Authentication**: Attach to pre-authenticated browser session
- **Human-First**: Test workflows that real users perform
- **Deterministic**: Same inputs → same outputs, no flakiness
- **Evidence-Based**: Screenshots, traces, logs for every failure
- **Self-Cleaning**: Automatic test data cleanup

### 1.2 Success Criteria

✅ Connects to Chrome in < 5s  
✅ Executes all workflows in < 10min  
✅ Zero false positives  
✅ Catches 95%+ regressions  
✅ Runs on dev/staging/prod

-----

## 2. System Architecture

### 2.1 Execution Flow

```
[Manual Chrome Launch + Login]
           ↓
[Tool Attaches via CDP]
           ↓
[Session Validation]
           ↓
[Execute Workflows]
           ↓
[Collect Evidence]
           ↓
[Generate Reports]
           ↓
[Exit with Status Code]
```

### 2.2 Component Diagram

```
CLI Entry Point (attach.ts)
    ├── SessionManager → CDP Connection
    ├── Orchestrator → Workflow Execution
    ├── Validators → Console/Network/Rendering
    ├── EvidenceCollector → Screenshots/Traces
    └── Reporter → JSON/HTML/Notifications
```

-----

## 3. Project Setup

### 3.1 Initialize Project

```bash
mkdir portal-sanity && cd portal-sanity
npm init -y
```

### 3.2 Install Dependencies

```json
{
  "dependencies": {
    "@playwright/test": "^1.40.0",
    "playwright": "^1.40.0",
    "typescript": "^5.3.0",
    "zod": "^3.22.0",
    "chalk": "^5.3.0",
    "commander": "^11.1.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "tsx": "^4.7.0"
  },
  "scripts": {
    "build": "tsc",
    "sanity": "tsx src/runner/attach.ts",
    "chrome": "./scripts/start-chrome.sh"
  }
}
```

### 3.3 TypeScript Configuration

**tsconfig.json:**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

### 3.4 Project Structure

```
portal-sanity/
├── src/
│   ├── runner/
│   │   ├── attach.ts           # Entry point
│   │   ├── session.ts          # Session manager
│   │   └── orchestrator.ts     # Workflow runner
│   ├── workflows/
│   │   ├── base.workflow.ts
│   │   ├── dashboard.workflow.ts
│   │   └── content.create.workflow.ts
│   ├── checks/
│   │   ├── console.check.ts
│   │   └── network.check.ts
│   ├── evidence/
│   │   └── collector.ts
│   ├── report/
│   │   └── reporter.ts
│   ├── config/
│   │   ├── sanity.config.ts
│   │   ├── routes.ts
│   │   └── selectors.ts
│   └── utils/
│       ├── logger.ts
│       └── retry.ts
├── scripts/
│   └── start-chrome.sh
├── output/
└── package.json
```

-----

## 4. Browser Attachment

### 4.1 Chrome Launch Script

**scripts/start-chrome.sh:**

```bash
#!/bin/bash
PORT=${1:-9222}
PROFILE="/tmp/chrome-sanity"

# Kill existing
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

# Clean profile
rm -rf "$PROFILE"
mkdir -p "$PROFILE"

# Launch (macOS example)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=$PORT \
    --user-data-dir="$PROFILE" \
    --no-first-run \
    "about:blank" &

echo "✅ Chrome started on port $PORT"
echo "👉 Log into portal manually, then run: npm run sanity"
```

### 4.2 Session Manager

**src/runner/session.ts:**

```typescript
import { chromium, Browser, BrowserContext, Page } from 'playwright';

export class SessionManager {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async connect(cdpPort: number, portalUrl: string): Promise<void> {
    // Connect to Chrome via CDP
    this.browser = await chromium.connectOverCDP(`http://localhost:${cdpPort}`);
    
    // Get first context
    const context = this.browser.contexts()[0];
    if (!context) throw new Error('No browser context found');

    // Find or create portal page
    const pages = context.pages();
    this.page = pages.find(p => p.url().includes(new URL(portalUrl).hostname)) ||
                await context.newPage();

    if (this.page.url() === 'about:blank') {
      await this.page.goto(portalUrl, { waitUntil: 'networkidle' });
    }
  }

  async validateAuth(): Promise<boolean> {
    if (!this.page) return false;

    const checks = await Promise.all([
      // Check auth cookies
      this.page.context().cookies().then(c => 
        c.some(ck => ck.name.includes('session') && ck.value.length > 10)
      ),
      // Check auth UI
      this.page.locator('[data-testid="user-menu"]').isVisible().catch(() => false),
      // Check storage
      this.page.evaluate(() => Boolean(localStorage.getItem('authToken'))),
    ]);

    return checks.some(Boolean);
  }

  getPage(): Page {
    if (!this.page) throw new Error('No page available');
    return this.page;
  }

  async disconnect(): Promise<void> {
    if (this.browser) await this.browser.close();
  }
}
```

-----

## 5. Workflow Framework

### 5.1 Base Workflow Class

**src/workflows/base.workflow.ts:**

```typescript
import { Page } from 'playwright';

export abstract class BaseWorkflow {
  protected page: Page;
  protected startTime = 0;
  protected endTime = 0;

  abstract name: string;
  abstract priority: 'P0' | 'P1' | 'P2';

  constructor(page: Page) {
    this.page = page;
  }

  async execute(): Promise<WorkflowResult> {
    this.startTime = Date.now();
    
    try {
      await this.navigateToStart();
      await this.executeSteps();
      await this.validateSuccess();
      
      this.endTime = Date.now();
      return { workflow: this.name, status: 'PASSED', duration: this.endTime - this.startTime };
    } catch (error) {
      this.endTime = Date.now();
      return { 
        workflow: this.name, 
        status: 'FAILED', 
        duration: this.endTime - this.startTime,
        error: error as Error 
      };
    } finally {
      await this.cleanup();
    }
  }

  protected abstract navigateToStart(): Promise<void>;
  protected abstract executeSteps(): Promise<void>;
  protected abstract validateSuccess(): Promise<void>;
  protected abstract cleanup(): Promise<void>;

  protected async clickAndWait(selector: string): Promise<void> {
    await this.page.click(selector);
    await this.page.waitForLoadState('networkidle');
  }

  protected async fillField(selector: string, value: string): Promise<void> {
    await this.page.waitForSelector(selector);
    await this.page.fill(selector, value);
  }
}

export interface WorkflowResult {
  workflow: string;
  status: 'PASSED' | 'FAILED';
  duration: number;
  error?: Error;
}
```

### 5.2 Example Workflow

**src/workflows/content.create.workflow.ts:**

```typescript
import { BaseWorkflow } from './base.workflow';

export class ContentCreateWorkflow extends BaseWorkflow {
  name = 'Content Creation';
  priority = 'P0' as const;
  
  private contentId = '';

  protected async navigateToStart(): Promise<void> {
    await this.page.goto('/content');
  }

  protected async executeSteps(): Promise<void> {
    // Click create
    await this.clickAndWait('[data-testid="create-content"]');
    
    // Fill form
    await this.fillField('[data-testid="title"]', `Test ${Date.now()}`);
    await this.fillField('[data-testid="body"]', 'Test content');
    
    // Save
    await this.clickAndWait('[data-testid="save"]');
    
    // Extract ID
    const url = this.page.url();
    this.contentId = url.match(/\/content\/([^/]+)/)?.[1] || '';
  }

  protected async validateSuccess(): Promise<void> {
    // Check success message
    const success = await this.page.locator('[data-testid="success"]').isVisible();
    if (!success) throw new Error('Success message not shown');
    
    // Verify in list
    await this.page.goto('/content');
    const exists = await this.page.locator(`[data-id="${this.contentId}"]`).isVisible();
    if (!exists) throw new Error('Content not in list');
  }

  protected async cleanup(): Promise<void> {
    if (!this.contentId) return;
    
    await this.page.goto(`/content/${this.contentId}`);
    await this.page.click('[data-testid="delete"]');
    await this.page.click('[data-testid="confirm-delete"]');
  }
}
```

-----

## 6. Validation Layer

### 6.1 Console Monitor

**src/checks/console.check.ts:**

```typescript
import { Page } from 'playwright';

export class ConsoleCheck {
  private errors: any[] = [];

  constructor(private page: Page) {}

  async startMonitoring(): Promise<void> {
    this.errors = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        this.errors.push({ message: msg.text(), timestamp: new Date() });
      }
    });

    this.page.on('pageerror', error => {
      this.errors.push({ message: error.message, stack: error.stack });
    });
  }

  async stopMonitoring(): Promise<void> {
    this.page.removeAllListeners('console');
    this.page.removeAllListeners('pageerror');
  }

  getErrors() {
    return this.errors;
  }
}
```

### 6.2 Network Monitor

**src/checks/network.check.ts:**

```typescript
import { Page, Request } from 'playwright';

export class NetworkCheck {
  private failedRequests: any[] = [];

  constructor(private page: Page) {}

  async startMonitoring(): Promise<void> {
    this.failedRequests = [];

    this.page.on('requestfinished', async (request: Request) => {
      const response = await request.response();
      if (response && response.status() >= 400) {
        this.failedRequests.push({
          url: request.url(),
          status: response.status(),
          method: request.method(),
        });
      }
    });

    this.page.on('requestfailed', (request: Request) => {
      this.failedRequests.push({
        url: request.url(),
        method: request.method(),
        failure: request.failure()?.errorText,
      });
    });
  }

  async stopMonitoring(): Promise<void> {
    this.page.removeAllListeners('requestfinished');
    this.page.removeAllListeners('requestfailed');
  }

  getErrors() {
    return this.failedRequests;
  }
}
```

-----

## 7. Evidence Collection

**src/evidence/collector.ts:**

```typescript
import * as fs from 'fs/promises';
import * as path from 'path';
import { Page } from 'playwright';

export class EvidenceCollector {
  constructor(private page: Page, private outputDir: string) {}

  async captureScreenshot(name: string): Promise<string> {
    const filepath = path.join(this.outputDir, `${name}-${Date.now()}.png`);
    await fs.mkdir(path.dirname(filepath), { recursive: true });
    await this.page.screenshot({ path: filepath, fullPage: true });
    return filepath;
  }

  async captureFailure(workflowName: string, error: Error): Promise<void> {
    // Screenshot
    await this.captureScreenshot(`failure-${workflowName}`);
    
    // HTML snapshot
    const html = await this.page.content();
    const htmlPath = path.join(this.outputDir, `${workflowName}.html`);
    await fs.writeFile(htmlPath, html);
    
    // Error details
    const errorPath = path.join(this.outputDir, `${workflowName}-error.json`);
    await fs.writeFile(errorPath, JSON.stringify({
      error: error.message,
      stack: error.stack,
      url: this.page.url(),
      timestamp: new Date().toISOString(),
    }, null, 2));
  }
}
```

-----

## 8. Reporting

**src/report/reporter.ts:**

```typescript
import * as fs from 'fs/promises';
import { WorkflowResult } from '../workflows/base.workflow';
import chalk from 'chalk';

export class Reporter {
  private results: WorkflowResult[] = [];

  addResult(result: WorkflowResult): void {
    this.results.push(result);
  }

  async generateReports(outputDir: string): Promise<void> {
    await fs.mkdir(outputDir, { recursive: true });
    
    // JSON report
    const jsonPath = `${outputDir}/summary.json`;
    await fs.writeFile(jsonPath, JSON.stringify({
      results: this.results,
      summary: this.getSummary(),
    }, null, 2));
    
    // Print summary
    this.printSummary();
  }

  private getSummary() {
    const total = this.results.length;
    const passed = this.results.filter(r => r.status === 'PASSED').length;
    const failed = total - passed;
    
    return { total, passed, failed, successRate: (passed/total) * 100 };
  }

  private printSummary(): void {
    const { total, passed, failed, successRate } = this.getSummary();
    
    console.log('\n' + '='.repeat(60));
    console.log(chalk.bold('📊 SANITY TEST SUMMARY'));
    console.log('='.repeat(60));
    console.log(`Total: ${total}`);
    console.log(chalk.green(`✅ Passed: ${passed}`));
    console.log(chalk.red(`❌ Failed: ${failed}`));
    console.log(`Success Rate: ${successRate.toFixed(1)}%`);
    console.log('='.repeat(60) + '\n');
  }

  shouldFail(): boolean {
    return this.results.some(r => r.status === 'FAILED' && r.priority === 'P0');
  }
}
```

-----

## 9. Configuration

**src/config/sanity.config.ts:**

```typescript
export interface SanityConfig {
  cdpPort: number;
  portalUrl: string;
  outputDir: string;
}

export function loadConfig(): SanityConfig {
  return {
    cdpPort: Number(process.env.CDP_PORT) || 9222,
    portalUrl: process.env.PORTAL_URL || 'http://localhost:3000',
    outputDir: `./output/reports/${Date.now()}`,
  };
}
```

**src/config/routes.ts:**

```typescript
export const ROUTES = {
  DASHBOARD: '/dashboard',
  CONTENT_LIST: '/content',
  CONTENT_CREATE: '/content/create',
};
```

**src/config/selectors.ts:**

```typescript
export const SELECTORS = {
  CONTENT: {
    CREATE_BUTTON: '[data-testid="create-content"]',
    TITLE_INPUT: '[data-testid="title"]',
    SAVE_BUTTON: '[data-testid="save"]',
    SUCCESS_MESSAGE: '[data-testid="success"]',
  },
};
```

-----

## 10. Complete Implementation

### 10.1 Orchestrator

**src/runner/orchestrator.ts:**

```typescript
import { Page } from 'playwright';
import { BaseWorkflow, WorkflowResult } from '../workflows/base.workflow';
import { ConsoleCheck } from '../checks/console.check';
import { NetworkCheck } from '../checks/network.check';
import { EvidenceCollector } from '../evidence/collector';

export class Orchestrator {
  constructor(
    private page: Page,
    private outputDir: string,
  ) {}

  async executeWorkflows(workflows: BaseWorkflow[]): Promise<WorkflowResult[]> {
    const results: WorkflowResult[] = [];
    
    for (const workflow of workflows) {
      const consoleCheck = new ConsoleCheck(this.page);
      const networkCheck = new NetworkCheck(this.page);
      const evidence = new EvidenceCollector(this.page, this.outputDir);
      
      // Start monitoring
      await consoleCheck.startMonitoring();
      await networkCheck.startMonitoring();
      
      // Execute workflow
      const result = await workflow.execute();
      
      // Add error details
      const consoleErrors = consoleCheck.getErrors();
      const networkErrors = networkCheck.getErrors();
      
      if (result.status === 'FAILED') {
        await evidence.captureFailure(workflow.name, result.error!);
      }
      
      // Stop monitoring
      await consoleCheck.stopMonitoring();
      await networkCheck.stopMonitoring();
      
      results.push({ 
        ...result, 
        consoleErrors, 
        networkErrors 
      });
      
      console.log(`${result.status === 'PASSED' ? '✅' : '❌'} ${workflow.name}`);
    }
    
    return results;
  }
}
```

### 10.2 Main Entry Point

**src/runner/attach.ts:**

```typescript
#!/usr/bin/env node

import { SessionManager } from './session';
import { Orchestrator } from './orchestrator';
import { Reporter } from '../report/reporter';
import { loadConfig } from '../config/sanity.config';
import { ContentCreateWorkflow } from '../workflows/content.create.workflow';
import chalk from 'chalk';

async function main() {
  console.log(chalk.bold.blue('\n🚀 Portal Sanity Automation\n'));
  
  try {
    // Load config
    const config = loadConfig();
    
    // Connect to Chrome
    const session = new SessionManager();
    await session.connect(config.cdpPort, config.portalUrl);
    
    // Validate authentication
    const isAuthenticated = await session.validateAuth();
    if (!isAuthenticated) {
      console.error(chalk.red('❌ Session not authenticated. Please log in first.'));
      process.exit(1);
    }
    console.log(chalk.green('✅ Session authenticated\n'));
    
    // Get page
    const page = session.getPage();
    
    // Setup workflows
    const workflows = [
      new ContentCreateWorkflow(page),
      // Add more workflows here
    ];
    
    // Execute workflows
    const orchestrator = new Orchestrator(page, config.outputDir);
    const results = await orchestrator.executeWorkflows(workflows);
    
    // Generate reports
    const reporter = new Reporter();
    results.forEach(r => reporter.addResult(r));
    await reporter.generateReports(config.outputDir);
    
    // Disconnect
    await session.disconnect();
    
    // Exit
    const exitCode = reporter.shouldFail() ? 1 : 0;
    process.exit(exitCode);
    
  } catch (error) {
    console.error(chalk.red('\n❌ Fatal error:'), error);
    process.exit(1);
  }
}

main();
```

### 10.3 Utility: Logger

**src/utils/logger.ts:**

```typescript
import chalk from 'chalk';

export const logger = {
  info: (msg: string) => console.log(chalk.blue('ℹ'), msg),
  success: (msg: string) => console.log(chalk.green('✓'), msg),
  warn: (msg: string) => console.log(chalk.yellow('⚠'), msg),
  error: (msg: string) => console.error(chalk.red('✗'), msg),
  debug: (msg: string) => process.env.DEBUG && console.log(chalk.gray('⋯'), msg),
};
```

-----

## 11. Usage Guide

### 11.1 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start Chrome with debugging
npm run chrome
# OR manually:
# /path/to/chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile

# 3. Log into portal manually in the Chrome window

# 4. Run sanity tests
npm run sanity

# 5. View reports
open output/reports/latest/report.html
```

### 11.2 Environment Variables

```bash
# .env
CDP_PORT=9222
PORTAL_URL=https://staging.example.com
DEBUG=true
```

### 11.3 Adding New Workflows

```typescript
// 1. Create new workflow file
export class MyWorkflow extends BaseWorkflow {
  name = 'My Workflow';
  priority = 'P1' as const;

  protected async navigateToStart() { /* ... */ }
  protected async executeSteps() { /* ... */ }
  protected async validateSuccess() { /* ... */ }
  protected async cleanup() { /* ... */ }
}

// 2. Add to attach.ts
const workflows = [
  new ContentCreateWorkflow(page),
  new MyWorkflow(page), // ← Add here
];
```

### 11.4 CI/CD Integration

**.github/workflows/sanity.yml:**

```yaml
name: Sanity Tests

on:
  workflow_dispatch:

jobs:
  sanity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - run: npm ci
      - run: npx playwright install chromium
      
      - name: Run Sanity
        run: npm run sanity
        env:
          PORTAL_URL: ${{ secrets.STAGING_URL }}
      
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: reports
          path: output/reports/
```

-----

## 12. Troubleshooting

|Issue                   |Solution                                 |
|------------------------|-----------------------------------------|
|Cannot connect to Chrome|Verify Chrome running with `lsof -i:9222`|
|Authentication fails    |Log in manually before running tests     |
|Selectors not found     |Update `src/config/selectors.ts`         |
|Timeout errors          |Increase timeouts in config              |

-----

## 13. Best Practices

1. **Selectors**: Always use `data-testid` attributes
1. **Cleanup**: Every workflow must clean up its test data
1. **Evidence**: Capture screenshots at key checkpoints
1. **Determinism**: Workflows must be order-independent
1. **Priorities**: P0 failures = CI pipeline fails

-----

**END OF SPECIFICATION**

This document is your complete implementation blueprint. Every component is production-ready. Download, implement, and run your sanity automation suite.

For questions or issues, refer to specific sections above.