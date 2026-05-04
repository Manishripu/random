# Angular Library Sharing via Jenkins + S3 + CloudFront

> A complete, production-ready guide to building, packaging, and consuming an Angular 19 library across repositories using Jenkins CI, AWS S3 artifact storage, and CloudFront CDN — no npm registry required.

-----

## Table of Contents

1. [Architecture Overview](#architecture-overview)
1. [Prerequisites](#prerequisites)
1. [Phase 1 — Create the Library (Repo A)](#phase-1--create-the-library-repo-a)
1. [Phase 2 — Build the Library](#phase-2--build-the-library)
1. [Phase 3 — Package as `.tgz`](#phase-3--package-as-tgz)
1. [Phase 4 — Publish via Jenkins to S3](#phase-4--publish-via-jenkins-to-s3)
1. [Phase 5 — Serve via CloudFront](#phase-5--serve-via-cloudfront)
1. [Phase 6 — Consume in Repo B](#phase-6--consume-in-repo-b)
1. [Phase 7 — Updating the Library](#phase-7--updating-the-library)
1. [Secondary Entrypoints (Advanced)](#secondary-entrypoints-advanced)
1. [Best Practices](#best-practices)
1. [Common Mistakes](#common-mistakes)
1. [Limitations & Mitigations](#limitations--mitigations)
1. [Quick Reference Cheatsheet](#quick-reference-cheatsheet)

-----

## Architecture Overview

```
Developer (Repo A)
  └── projects/common-lib/          ← Library source
        ↓  git push
Git Remote (main / tag)
        ↓  triggers
Jenkins Pipeline
  ├── npm ci
  ├── ng build common-lib           ← Compiles to dist/
  ├── npm pack dist/common-lib      ← Produces your-org-common-lib-1.0.0.tgz
  └── aws s3 cp *.tgz s3://your-bucket/common-lib/1.0.0/
        ↓
AWS S3 (artifact storage)
        ↓  origin
AWS CloudFront (CDN)
  └── https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz
        ↓
Consumer (Repo B)
  └── npm install https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz
```

> **Key principle:** S3 paths are immutable and version-stamped. The same `1.0.0` URL always serves the same artifact. Never overwrite a published version.

-----

## Prerequisites

### Developer Machine

|Tool       |Minimum Version|Check Command   |
|-----------|---------------|----------------|
|Node.js    |18+            |`node --version`|
|npm        |9+             |`npm --version` |
|Angular CLI|19+            |`ng version`    |
|Git        |2.30+          |`git --version` |

```bash
npm install -g @angular/cli@19
```

### Jenkins Agent

|Tool              |Notes                                             |
|------------------|--------------------------------------------------|
|Node.js           |Install via `nvm` or Jenkins NodeJS plugin        |
|AWS CLI v2        |Must be configured with an IAM role or credentials|
|`ng` (Angular CLI)|Installed via `npm ci` in the pipeline            |

### AWS Resources Required

|Resource               |Purpose                                              |
|-----------------------|-----------------------------------------------------|
|S3 Bucket              |Stores versioned `.tgz` artifacts                    |
|CloudFront Distribution|CDN in front of S3 for fast, stable URLs             |
|IAM Role (Jenkins)     |`s3:PutObject`, `s3:GetObject` on the artifact bucket|

-----

## Phase 1 — Create the Library (Repo A)

### 1.1 — Generate the Angular Workspace

```bash
ng new repo-a --no-create-application
cd repo-a
git init
```

### 1.2 — Generate the Library

```bash
ng generate library common-lib
```

Resulting structure:

```
repo-a/
├── angular.json
├── package.json                  ← Workspace root (NOT for lib metadata)
├── tsconfig.json
└── projects/
    └── common-lib/
        ├── ng-package.json       ← ng-packagr config
        ├── package.json          ← ✅ Library name, version, peerDeps live here
        ├── tsconfig.lib.json
        ├── tsconfig.spec.json
        └── src/
            ├── public-api.ts     ← All public exports defined here
            └── lib/
                ├── common-lib.module.ts
                ├── common-lib.component.ts
                └── common-lib.service.ts
```

### 1.3 — Organise the Library Source

```
projects/common-lib/src/lib/
├── components/
│   ├── button/
│   │   ├── button.component.ts
│   │   ├── button.component.html
│   │   └── button.component.scss
│   └── modal/
│       └── ...
├── services/
│   ├── api.service.ts
│   └── auth.service.ts
├── models/
│   ├── user.model.ts
│   └── response.model.ts
├── utils/
│   ├── date.util.ts
│   └── string.util.ts
├── directives/
│   └── highlight.directive.ts
└── pipes/
    └── format.pipe.ts
```

### 1.4 — Configure the Public API

Edit `projects/common-lib/src/public-api.ts`:

```typescript
// Module
export * from './lib/common-lib.module';

// Components
export * from './lib/components/button/button.component';
export * from './lib/components/modal/modal.component';

// Services
export * from './lib/services/api.service';
export * from './lib/services/auth.service';

// Models
export * from './lib/models/user.model';
export * from './lib/models/response.model';

// Pipes
export * from './lib/pipes/format.pipe';
```

> ⚠️ Only export what is part of the public contract. Internal helpers and test utilities must NOT be exported.

### 1.5 — Configure Library `package.json`

Edit `projects/common-lib/package.json` — this file is what gets packed into the `.tgz`:

```json
{
  "name": "@your-org/common-lib",
  "version": "1.0.0",
  "description": "Shared Angular component and service library",
  "license": "MIT",
  "peerDependencies": {
    "@angular/common": "^19.0.0",
    "@angular/core": "^19.0.0",
    "@angular/forms": "^19.0.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0"
  },
  "peerDependenciesMeta": {
    "@angular/forms": {
      "optional": true
    }
  },
  "dependencies": {}
}
```

> ✅ `ng-packagr` reads this file and merges it with build output metadata into `dist/common-lib/package.json`. Do **not** add `main`, `module`, or `types` manually — the build tool sets them correctly.

-----

## Phase 2 — Build the Library

### 2.1 — Production Build

```bash
ng build common-lib --configuration production
```

Output in `dist/common-lib/`:

```
dist/common-lib/
├── package.json          ← Auto-generated by ng-packagr (has correct entry points)
├── index.d.ts
├── esm2022/
│   └── common-lib.mjs
├── fesm2022/
│   └── common-lib.mjs    ← Primary ESM bundle
├── lib/
│   └── **/*.d.ts         ← Type declarations
└── README.md
```

### 2.2 — Watch Mode (Local Development Only)

```bash
ng build common-lib --watch
```

Use this when developing the library locally alongside a consumer app. Not used in CI.

### 2.3 — Verify the Build Output

```bash
# Confirm entry points are correctly set
cat dist/common-lib/package.json

# Confirm public types are exported
grep "export" dist/common-lib/index.d.ts
```

-----

## Phase 3 — Package as `.tgz`

### 3.1 — Why `npm pack`?

`npm pack` creates a `.tgz` that is identical to what `npm publish` would push to a registry. It:

- Respects `.npmignore` (excludes source files, test files, etc.)
- Runs `prepublish` / `prepare` hooks if defined
- Produces a deterministic, self-contained artifact

### 3.2 — Run `npm pack`

Always run from inside the `dist/` output — not from the source directory:

```bash
cd dist/common-lib
npm pack
# Output: your-org-common-lib-1.0.0.tgz
```

Or from the repo root:

```bash
npm pack dist/common-lib
# Output: your-org-common-lib-1.0.0.tgz (in root)
```

### 3.3 — Verify the Package Contents

Before uploading, inspect what’s inside the `.tgz`:

```bash
tar -tzf your-org-common-lib-1.0.0.tgz
```

You should see only compiled output — no `src/`, no `node_modules/`, no test files.

### 3.4 — Naming Convention

Always name the artifact with a version to ensure immutability:

```
your-org-common-lib-{version}.tgz
# Example:
your-org-common-lib-1.0.0.tgz
your-org-common-lib-1.1.0.tgz
```

-----

## Phase 4 — Publish via Jenkins to S3

### 4.1 — S3 Bucket Structure

Use a consistent, versioned path structure:

```
s3://your-artifact-bucket/
└── common-lib/
    ├── 1.0.0/
    │   └── your-org-common-lib-1.0.0.tgz
    ├── 1.1.0/
    │   └── your-org-common-lib-1.1.0.tgz
    └── latest/
        └── your-org-common-lib-latest.tgz   ← Optional, for non-prod use only
```

> ⚠️ **Never overwrite a versioned path.** The `1.0.0/` folder is immutable once published. Only `latest/` may be overwritten.

### 4.2 — Jenkinsfile

Create a `Jenkinsfile` in the repo root:

```groovy
pipeline {
  agent any

  environment {
    S3_BUCKET       = 'your-artifact-bucket'
    S3_PREFIX       = 'common-lib'
    CDN_BASE        = 'https://cdn.your-org.com'
    NODE_VERSION    = '20'
  }

  stages {

    stage('Setup') {
      steps {
        sh "nvm use ${NODE_VERSION} || nvm install ${NODE_VERSION}"
        sh 'npm ci'
      }
    }

    stage('Test') {
      steps {
        sh 'ng test common-lib --watch=false --browsers=ChromeHeadless'
        sh 'ng lint common-lib'
      }
    }

    stage('Build') {
      steps {
        sh 'ng build common-lib --configuration production'
      }
    }

    stage('Pack') {
      steps {
        script {
          // Read version from the library's package.json
          def libPkg = readJSON file: 'projects/common-lib/package.json'
          env.LIB_VERSION = libPkg.version
          env.TGZ_NAME    = "your-org-common-lib-${env.LIB_VERSION}.tgz"
        }
        sh 'npm pack dist/common-lib'
        sh "ls -lh ${env.TGZ_NAME}"   // Sanity check the file exists
      }
    }

    stage('Upload to S3') {
      steps {
        sh """
          # Upload versioned artifact (immutable)
          aws s3 cp ${env.TGZ_NAME} \
            s3://${S3_BUCKET}/${S3_PREFIX}/${env.LIB_VERSION}/${env.TGZ_NAME} \
            --cache-control "public, max-age=31536000, immutable"

          # Also update the 'latest' pointer (mutable, for dev/testing only)
          aws s3 cp ${env.TGZ_NAME} \
            s3://${S3_BUCKET}/${S3_PREFIX}/latest/your-org-common-lib-latest.tgz \
            --cache-control "public, max-age=300"
        """
      }
    }

    stage('Notify') {
      steps {
        script {
          def cdnUrl = "${CDN_BASE}/${S3_PREFIX}/${env.LIB_VERSION}/${env.TGZ_NAME}"
          echo "✅ Published: ${cdnUrl}"
          // Optionally: post to Slack, update a manifest file, etc.
        }
      }
    }
  }

  post {
    failure {
      echo '❌ Pipeline failed — artifact was NOT published.'
    }
    cleanup {
      sh 'rm -f *.tgz'   // Clean up local tgz from workspace
    }
  }
}
```

### 4.3 — Jenkins Trigger Options

|Trigger                    |When to Use                              |
|---------------------------|-----------------------------------------|
|Push to `main` branch      |Publish a `latest` snapshot automatically|
|Git tag `v*.*.*`           |Publish a versioned, immutable release   |
|Manual build with parameter|For hotfixes or one-off releases         |

For tag-triggered releases, add to the pipeline:

```groovy
triggers {
  // Only run the full publish on version tags
  githubPush()
}
```

And in the `Upload to S3` stage, guard the versioned upload:

```groovy
when {
  tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
}
```

### 4.4 — IAM Policy for Jenkins

The Jenkins IAM role needs minimum permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-artifact-bucket",
        "arn:aws:s3:::your-artifact-bucket/common-lib/*"
      ]
    }
  ]
}
```

-----

## Phase 5 — Serve via CloudFront

### 5.1 — CloudFront Setup

Configure CloudFront with S3 as the origin:

|Setting                       |Value                                      |
|------------------------------|-------------------------------------------|
|Origin domain                 |`your-artifact-bucket.s3.amazonaws.com`    |
|Origin access                 |Origin Access Control (OAC) — not public S3|
|Viewer protocol               |HTTPS only                                 |
|Cache policy — versioned paths|`max-age=31536000, immutable`              |
|Cache policy — latest path    |`max-age=300`                              |


> ✅ Use **Origin Access Control (OAC)** so the S3 bucket is NOT public. Only CloudFront can read it.

### 5.2 — URL Structure

After setup, artifacts are accessible at:

```
# Versioned (immutable) — use this in production consumers
https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz

# Latest (mutable) — use only in dev/testing pipelines
https://cdn.your-org.com/common-lib/latest/your-org-common-lib-latest.tgz
```

### 5.3 — Access Control (Optional)

If the library contains proprietary code, restrict CloudFront access using **signed URLs** or **signed cookies** rather than making the distribution public:

```bash
# Generate a signed URL (valid for 1 hour)
aws cloudfront sign \
  --url "https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz" \
  --key-pair-id YOUR_KEY_PAIR_ID \
  --private-key file://private_key.pem \
  --date-less-than $(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)
```

For most internal teams, IP whitelisting via CloudFront WAF is simpler than signed URLs.

-----

## Phase 6 — Consume in Repo B

### 6.1 — Install the Library

```bash
# Install directly from the versioned CDN URL
npm install https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz
```

The resulting entry in Repo B’s `package.json`:

```json
{
  "dependencies": {
    "@your-org/common-lib": "https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz"
  }
}
```

> ✅ Because the URL is versioned and the file is immutable, `npm ci` in CI will always install the exact same artifact. No integrity drift.

### 6.2 — Register in `tsconfig.json`

```json
{
  "compilerOptions": {
    "paths": {
      "@your-org/common-lib": ["node_modules/@your-org/common-lib"]
    }
  }
}
```

### 6.3 — Import the Module

**NgModule-based app:**

```typescript
import { NgModule } from '@angular/core';
import { CommonLibModule } from '@your-org/common-lib';

@NgModule({
  imports: [CommonLibModule]
})
export class AppModule {}
```

**Standalone components (Angular 14+):**

```typescript
import { Component } from '@angular/core';
import { ButtonComponent } from '@your-org/common-lib';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ButtonComponent],
  template: `<lib-button>Click me</lib-button>`
})
export class AppComponent {}
```

### 6.4 — Use Services

```typescript
import { Component, inject } from '@angular/core';
import { ApiService } from '@your-org/common-lib';

@Component({ ... })
export class DashboardComponent {
  private api = inject(ApiService);

  ngOnInit() {
    this.api.getData().subscribe(data => console.log(data));
  }
}
```

### 6.5 — Verify Peer Dependencies

```bash
npm ls @angular/core   # Should show no version conflicts
```

-----

## Phase 7 — Updating the Library

### 7.1 — Release a New Version (Repo A)

```bash
# 1. Bump version in projects/common-lib/package.json
#    e.g. "version": "1.0.0"  →  "version": "1.1.0"

# 2. Commit the version bump
git add projects/common-lib/package.json
git commit -m "chore: bump lib version to 1.1.0"

# 3. Tag the release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --follow-tags
```

Jenkins picks up the tag, builds, packs, and uploads `your-org-common-lib-1.1.0.tgz` to S3 automatically.

### 7.2 — Update the Consumer (Repo B)

```bash
# Replace the old URL with the new version
npm install https://cdn.your-org.com/common-lib/1.1.0/your-org-common-lib-1.1.0.tgz
```

Update `package.json` and commit the lockfile:

```bash
git add package.json package-lock.json
git commit -m "chore: update common-lib to v1.1.0"
```

### 7.3 — Cache Busting

npm caches tarball installs. If a re-install isn’t picking up changes:

```bash
npm cache clean --force
npm install
```

Or in CI, always use `npm ci` (which ignores cache and uses the lockfile directly):

```bash
npm ci
```

-----

## Secondary Entrypoints (Advanced)

For tree-shakeable imports like:

```typescript
import { formatDate } from '@your-org/common-lib/utils';
```

### Structure

```
projects/common-lib/
├── src/                   ← Primary entrypoint
│   └── public-api.ts
├── utils/                 ← Secondary entrypoint
│   ├── src/
│   │   ├── index.ts
│   │   └── date.util.ts
│   └── ng-package.json
└── services/
    ├── src/
    │   ├── index.ts
    │   └── api.service.ts
    └── ng-package.json
```

### Secondary `ng-package.json`

```json
{
  "$schema": "../../../node_modules/ng-packagr/ng-package.schema.json",
  "lib": {
    "entryFile": "src/index.ts"
  }
}
```

`ng build common-lib` discovers and builds all secondary entrypoints automatically. The packed `.tgz` includes them.

-----

## Best Practices

### Versioning & Immutability

- **Always version S3 paths** — `common-lib/1.0.0/` not `common-lib/latest/`
- **Never overwrite a published version** — treat versioned S3 paths as immutable
- **Use annotated Git tags** — tag the source commit that produced each artifact
- **Maintain a `CHANGELOG.md`** — consumers can’t inspect the artifact’s commit history

### Pipeline Hygiene

- **Always run tests before packing** — never publish an untested artifact
- **Verify the `.tgz` contents** before uploading (`tar -tzf`)
- **Store the CDN URL in a manifest or wiki** so consumers can discover new versions
- **Clean up workspace artifacts** after upload (`rm -f *.tgz` in `post { cleanup }`)

### Library Design

- Use `peerDependencies` for Angular packages — never `dependencies`
- Set `"sideEffects": false` in `package.json` for better tree-shaking in consumers
- Keep the library decoupled from app-specific business logic
- Never import from `@angular/core/testing` in library source

-----

## Common Mistakes

|Mistake                                                           |Problem                                    |Fix                                                     |
|------------------------------------------------------------------|-------------------------------------------|--------------------------------------------------------|
|Using a mutable URL (`latest`) in production `package.json`       |Different installs get different code      |Always pin to a versioned URL                           |
|Running `npm pack` from source dir instead of `dist/`             |Packs raw TypeScript, not compiled output  |Always `npm pack dist/common-lib`                       |
|Overwriting an existing S3 version path                           |Breaks consumers on re-install             |S3 paths are immutable — bump the version               |
|Making the S3 bucket fully public                                 |Security risk for proprietary code         |Use CloudFront + OAC; never enable public S3            |
|Not setting `Cache-Control: immutable` on versioned files         |CloudFront re-fetches unnecessarily        |Set `max-age=31536000, immutable` for versioned paths   |
|Not running `npm ci` in consumer CI                               |Ignores lockfile, may install wrong version|Always use `npm ci` in CI pipelines                     |
|Forgetting to bump `version` in `projects/common-lib/package.json`|`.tgz` filename collides with old artifact |Enforce version bump as a required pipeline step        |
|Missing exports in `public-api.ts`                                |`TS2305: Module has no exported member`    |Export everything consumers need through `public-api.ts`|

-----

## Limitations & Mitigations

|Limitation                      |Severity|Mitigation                                                                       |
|--------------------------------|--------|---------------------------------------------------------------------------------|
|No `npm outdated` support       |Medium  |Maintain a version manifest or Slack notification when new versions are published|
|No `npm audit` for tarball deps |Medium  |Use Snyk or OWASP Dependency-Check as a separate pipeline step                   |
|Version discovery is manual     |Medium  |Automate release notes or a changelog notification to consumer teams             |
|CloudFront signed URLs expire   |Low     |Use IAM/WAF IP whitelisting instead for internal teams                           |
|Slower first install vs registry|Low     |npm caches tarballs after first install; use `npm ci` with a warm cache in CI    |
|No transitive dep resolution    |Low     |Explicit `peerDependencies` in the library covers this                           |

-----

## Quick Reference Cheatsheet

### Repo A — Bump & Tag a Release

```bash
# Bump version in projects/common-lib/package.json manually, then:
git add projects/common-lib/package.json
git commit -m "chore: bump lib to v1.x.x"
git tag -a v1.x.x -m "Release v1.x.x"
git push origin main --follow-tags
# Jenkins takes over from here ↑
```

### Jenkins — Core Build Steps

```bash
npm ci
ng test common-lib --watch=false --browsers=ChromeHeadless
ng build common-lib --configuration production
npm pack dist/common-lib
aws s3 cp your-org-common-lib-1.x.x.tgz \
  s3://your-bucket/common-lib/1.x.x/your-org-common-lib-1.x.x.tgz \
  --cache-control "public, max-age=31536000, immutable"
```

### Repo B — Install / Update

```bash
# Install specific version
npm install https://cdn.your-org.com/common-lib/1.0.0/your-org-common-lib-1.0.0.tgz

# Update to new version
npm install https://cdn.your-org.com/common-lib/1.1.0/your-org-common-lib-1.1.0.tgz

# Force clean install (CI)
npm ci
```

### Import Reference

```typescript
// NgModule-based
import { CommonLibModule } from '@your-org/common-lib';

// Standalone component
import { ButtonComponent } from '@your-org/common-lib';

// Service
import { ApiService } from '@your-org/common-lib';

// Secondary entrypoint (if configured)
import { formatDate } from '@your-org/common-lib/utils';
```

-----

*Last updated: v2.0 — Distribution method updated from Git-based to Jenkins + S3 + CloudFront `.tgz` pipeline.*