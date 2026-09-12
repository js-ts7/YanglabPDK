const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const CATEGORY_ORDER = [
  "waveguides", "bends", "couplers", "cavities", "filters", "mmis",
  "mzis", "reflectors", "lasers", "spirals", "tapers", "shapes", "utils", "other"
];

function findPackageRoot(extensionPath) {
  const configured = vscode.workspace.getConfiguration("yanglabPDK").get("packageRoot", "").trim();
  const candidates = [];
  if (configured) candidates.push(configured);
  for (const folder of vscode.workspace.workspaceFolders || []) {
    candidates.push(path.join(folder.uri.fsPath, "YanglabPDK"));
    candidates.push(folder.uri.fsPath);
  }
  candidates.push(path.resolve(extensionPath, ".."));
  return candidates.find(candidate =>
    fs.existsSync(path.join(candidate, "catalog", "components.json")) &&
    fs.existsSync(path.join(candidate, "components"))
  );
}

function loadCatalog(extensionPath, packageRoot) {
  const candidates = [
    packageRoot && path.join(packageRoot, "catalog", "components.json"),
    path.join(extensionPath, "resources", "components.json")
  ].filter(Boolean);
  const source = candidates.find(fs.existsSync);
  if (!source) throw new Error("components.json was not found. Run Refresh Catalog from a YanglabPDK workspace.");
  return { source, data: JSON.parse(fs.readFileSync(source, "utf8")) };
}

class ComponentTreeProvider {
  constructor(components) {
    this.components = components;
    this.query = "";
    this.changed = new vscode.EventEmitter();
    this.onDidChangeTreeData = this.changed.event;
  }

  setComponents(components) {
    this.components = components;
    this.changed.fire();
  }

  setQuery(query) {
    this.query = (query || "").trim().toLowerCase();
    this.changed.fire();
  }

  filtered() {
    if (!this.query) return this.components;
    return this.components.filter(item =>
      [item.name, item.title, item.category, item.description, item.module]
        .filter(Boolean).join(" ").toLowerCase().includes(this.query)
    );
  }

  getTreeItem(item) {
    if (item.kind === "group") {
      const treeItem = new vscode.TreeItem(item.label, vscode.TreeItemCollapsibleState.Expanded);
      treeItem.description = String(item.count);
      treeItem.iconPath = new vscode.ThemeIcon(item.discovered ? "beaker" : "symbol-namespace");
      return treeItem;
    }
    const treeItem = new vscode.TreeItem(item.title || item.name, vscode.TreeItemCollapsibleState.None);
    treeItem.description = item.name;
    treeItem.tooltip = new vscode.MarkdownString(`**${item.module}.${item.name}**\n\n${item.description || "No description yet."}`);
    treeItem.iconPath = new vscode.ThemeIcon(item.registered ? "symbol-method" : "question");
    treeItem.contextValue = "yanglabComponent";
    treeItem.command = { command: "yanglabPdk.showDetails", title: "Show Component", arguments: [item] };
    return treeItem;
  }

  getChildren(item) {
    const visible = this.filtered().filter(component => component.status !== "error");
    if (item && item.kind === "group") return item.items;
    if (item) return [];
    const registered = visible.filter(component => component.registered);
    const groups = [...new Set(registered.map(component => component.category))]
      .sort((a, b) => {
        const ai = CATEGORY_ORDER.indexOf(a); const bi = CATEGORY_ORDER.indexOf(b);
        return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi) || a.localeCompare(b);
      })
      .map(category => {
        const items = registered.filter(component => component.category === category);
        return { kind: "group", label: category, count: items.length, items };
      });
    const unclassified = visible.filter(component => !component.registered);
    if (unclassified.length) groups.push({ kind: "group", label: "Unclassified", count: unclassified.length, items: unclassified, discovered: true });
    return groups;
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function displayValue(parameter) {
  if (parameter.kind === "required") return "";
  if (parameter.kind === "literal") {
    if (parameter.value === null) return "None";
    if (parameter.value === true) return "True";
    if (parameter.value === false) return "False";
    if (typeof parameter.value === "string") return JSON.stringify(parameter.value);
  }
  return parameter.source || JSON.stringify(parameter.value);
}

class DetailsProvider {
  constructor(extensionUri, getPackageRoot) {
    this.extensionUri = extensionUri;
    this.getPackageRoot = getPackageRoot;
    this.component = undefined;
  }

  resolveWebviewView(view) {
    this.view = view;
    const roots = [this.extensionUri, ...(vscode.workspace.workspaceFolders || []).map(folder => folder.uri)];
    view.webview.options = { enableScripts: true, localResourceRoots: roots };
    view.webview.onDidReceiveMessage(message => {
      if (message.type === "insert" && this.component) {
        vscode.commands.executeCommand("yanglabPdk.insertComponent", this.component, message.parameters);
      } else if (message.type === "copy" && this.component) {
        vscode.env.clipboard.writeText(buildPlainCode(this.component, message.parameters));
        vscode.window.showInformationMessage(`Copied ${this.component.name} example.`);
      } else if (message.type === "source" && this.component) {
        vscode.commands.executeCommand("yanglabPdk.openSource", this.component);
      }
    });
    this.render();
  }

  show(component) {
    this.component = component;
    if (this.view) {
      this.render();
      this.view.show?.(true);
    }
  }

  thumbnailUri(component) {
    const filename = path.basename(component.thumbnail || `${component.name}.png`);
    const packageRoot = this.getPackageRoot();
    const candidates = [
      packageRoot && vscode.Uri.file(path.join(packageRoot, "catalog_assets", "thumbnails", filename)),
      vscode.Uri.joinPath(this.extensionUri, "resources", "thumbnails", filename)
    ].filter(Boolean);
    const local = candidates.find(uri => fs.existsSync(uri.fsPath));
    return local && this.view ? this.view.webview.asWebviewUri(local) : undefined;
  }

  render() {
    if (!this.view) return;
    const component = this.component;
    if (!component) {
      this.view.webview.html = this.shell(`<div class="empty"><span class="codicon codicon-circuit-board"></span><p>Select a component to inspect its parameters and insert code.</p></div>`);
      return;
    }
    const thumbnail = this.thumbnailUri(component);
    const recommended = new Set(component.recommended || []);
    const rows = (component.parameters || []).map((parameter, index) => {
      const checked = recommended.has(parameter.name) || parameter.kind === "required";
      const value = displayValue(parameter);
      return `<label class="parameter ${checked ? "common" : "advanced"}">
        <input class="include" type="checkbox" data-name="${escapeHtml(parameter.name)}" ${checked ? "checked" : ""}>
        <span class="parameter-name">${escapeHtml(parameter.name)}</span>
        <input class="value" type="text" data-name="${escapeHtml(parameter.name)}" value="${escapeHtml(value)}" placeholder="${parameter.kind === "required" ? "required" : "default"}">
        <small>${escapeHtml(parameter.annotation || "")}</small>
      </label>`;
    }).join("");
    this.view.webview.html = this.shell(`
      <header><span class="badge">${escapeHtml(component.category)}</span><h2>${escapeHtml(component.title)}</h2><code>${escapeHtml(component.name)}</code></header>
      ${thumbnail ? `<img class="preview" src="${thumbnail}" alt="${escapeHtml(component.title)} layout preview">` : `<div class="preview missing">Preview not generated</div>`}
      <p>${escapeHtml(component.description || "No description yet.")}</p>
      <div class="module"><code>${escapeHtml(component.module)}.${escapeHtml(component.name)}</code></div>
      <div class="section-title"><strong>Parameters</strong><button id="toggleAdvanced" class="link">Show advanced</button></div>
      <div id="parameters">${rows || "<p>No parameters.</p>"}</div>
      <div class="actions"><button id="insert" class="primary">Insert Code</button><button id="copy">Copy Example</button><button id="source">Source</button></div>
      <p class="hint">Checked parameters are inserted. Use Tab to move through snippet values.</p>
      <script>
        const vscode = acquireVsCodeApi();
        let advanced = false;
        const collect = () => [...document.querySelectorAll('.parameter')].filter(row => row.querySelector('.include').checked).map(row => ({name: row.querySelector('.include').dataset.name, value: row.querySelector('.value').value}));
        document.getElementById('insert').onclick = () => vscode.postMessage({type: 'insert', parameters: collect()});
        document.getElementById('copy').onclick = () => vscode.postMessage({type: 'copy', parameters: collect()});
        document.getElementById('source').onclick = () => vscode.postMessage({type: 'source'});
        document.getElementById('toggleAdvanced').onclick = event => { advanced = !advanced; document.body.classList.toggle('show-advanced', advanced); event.target.textContent = advanced ? 'Hide advanced' : 'Show advanced'; };
      </script>`);
  }

  shell(body) {
    return `<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
      body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);padding:10px;margin:0} h2{font-size:17px;margin:6px 0 2px} p{line-height:1.45} code{font-family:var(--vscode-editor-font-family);font-size:12px} .badge{font-size:10px;text-transform:uppercase;color:var(--vscode-descriptionForeground)}
      .preview{box-sizing:border-box;width:100%;max-height:220px;object-fit:contain;margin:12px 0;background:var(--vscode-editor-background);border:1px solid var(--vscode-panel-border);border-radius:4px}.missing{height:110px;display:flex;align-items:center;justify-content:center;color:var(--vscode-descriptionForeground)}
      .module{overflow-wrap:anywhere;padding:8px;background:var(--vscode-textCodeBlock-background);border-radius:3px}.section-title{display:flex;justify-content:space-between;align-items:center;margin-top:14px}.link{border:0;background:none;color:var(--vscode-textLink-foreground);cursor:pointer}.parameter{display:grid;grid-template-columns:20px minmax(90px,1fr) minmax(90px,1.4fr);gap:5px;align-items:center;margin:7px 0}.parameter.advanced{display:none}.show-advanced .parameter.advanced{display:grid}.parameter input.value{min-width:0;color:var(--vscode-input-foreground);background:var(--vscode-input-background);border:1px solid var(--vscode-input-border);padding:4px}.parameter small{grid-column:2/4;color:var(--vscode-descriptionForeground)}
      .actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}.actions button{padding:5px 9px;color:var(--vscode-button-secondaryForeground);background:var(--vscode-button-secondaryBackground);border:0;border-radius:2px;cursor:pointer}.actions .primary{color:var(--vscode-button-foreground);background:var(--vscode-button-background)}.hint,.empty{color:var(--vscode-descriptionForeground);font-size:12px}.empty{text-align:center;padding:24px 6px}
    </style></head><body>${body}</body></html>`;
  }
}

function selectedParameters(component, supplied) {
  if (Array.isArray(supplied)) return supplied;
  const recommended = new Set(component.recommended || []);
  return (component.parameters || []).filter(item => recommended.has(item.name) || item.kind === "required").map(item => ({ name: item.name, value: displayValue(item) }));
}

function safeValue(value) {
  return String(value || "None").replace(/\\/g, "\\\\").replace(/\$/g, "\\$").replace(/}/g, "\\}");
}

function buildSnippet(component, supplied) {
  const parameters = selectedParameters(component, supplied);
  const variable = component.name.replace(/[^A-Za-z0-9_]/g, "_");
  if (!parameters.length) return `${variable} = ${component.name}()`;
  const lines = parameters.map((item, index) => `    ${item.name}=\${${index + 1}:${safeValue(item.value)}},`);
  return `${variable} = ${component.name}(\n${lines.join("\n")}\n)`;
}

function buildPlainCode(component, supplied) {
  const parameters = selectedParameters(component, supplied);
  const variable = component.name.replace(/[^A-Za-z0-9_]/g, "_");
  const call = parameters.length
    ? `${variable} = ${component.name}(\n${parameters.map(item => `    ${item.name}=${item.value || "None"},`).join("\n")}\n)`
    : `${variable} = ${component.name}()`;
  return `from ${component.module} import ${component.name}\n\n${call}`;
}

async function insertComponent(component, supplied) {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "python") {
    vscode.window.showWarningMessage("Open a Python file before inserting a YanglabPDK component.");
    return;
  }
  const importLine = `from ${component.module} import ${component.name}`;
  const text = editor.document.getText();
  if (!text.split(/\r?\n/).some(line => line.trim() === importLine)) {
    let insertLine = 0;
    const lines = text.split(/\r?\n/);
    if (lines[0]?.startsWith("#!")) insertLine = 1;
    if (lines[insertLine]?.match(/^#.*coding[:=]/)) insertLine += 1;
    await editor.edit(builder => builder.insert(new vscode.Position(insertLine, 0), `${importLine}\n`), { undoStopAfter: false });
  }
  await editor.insertSnippet(new vscode.SnippetString(buildSnippet(component, supplied)), editor.selection.active, { undoStopBefore: false });
}

async function pythonPathFor(resource) {
  const configured = vscode.workspace.getConfiguration("yanglabPDK").get("pythonPath", "").trim();
  if (configured) return configured;
  const pythonExtension = vscode.extensions.getExtension("ms-python.python");
  if (pythonExtension) {
    try {
      const api = await pythonExtension.activate();
      const active = api?.environments?.getActiveEnvironmentPath?.(resource);
      if (active?.path) return active.path;
    } catch (_) { /* fall through to settings */ }
  }
  return vscode.workspace.getConfiguration("python").get("defaultInterpreterPath", "") || "python";
}

function runProcess(executable, args, cwd) {
  return new Promise((resolve, reject) => {
    cp.execFile(executable, args, { cwd, windowsHide: true }, (error, stdout, stderr) => {
      if (error) reject(new Error(`${stderr || stdout || error.message}`.trim()));
      else resolve({ stdout, stderr });
    });
  });
}

function activate(context) {
  let packageRoot = findPackageRoot(context.extensionPath);
  let loaded = loadCatalog(context.extensionPath, packageRoot);
  const tree = new ComponentTreeProvider(loaded.data.components || []);
  const details = new DetailsProvider(context.extensionUri, () => packageRoot);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("yanglabPdk.components", tree),
    vscode.window.registerWebviewViewProvider("yanglabPdk.details", details),
    vscode.commands.registerCommand("yanglabPdk.showDetails", item => details.show(item)),
    vscode.commands.registerCommand("yanglabPdk.insertComponent", (item, parameters) => insertComponent(item, parameters)),
    vscode.commands.registerCommand("yanglabPdk.search", async () => {
      const query = await vscode.window.showInputBox({ prompt: "Search YanglabPDK components", placeHolder: "ring, coupler, MZI..." });
      if (query !== undefined) tree.setQuery(query);
    }),
    vscode.commands.registerCommand("yanglabPdk.clearSearch", () => tree.setQuery("")),
    vscode.commands.registerCommand("yanglabPdk.openSource", async item => {
      packageRoot = findPackageRoot(context.extensionPath);
      if (!packageRoot) return vscode.window.showErrorMessage("Open the YanglabPDK workspace or configure yanglabPDK.packageRoot.");
      const document = await vscode.workspace.openTextDocument(path.join(packageRoot, item.file));
      const editor = await vscode.window.showTextDocument(document, { preview: true });
      editor.revealRange(new vscode.Range(Math.max(0, item.line - 1), 0, Math.max(0, item.line - 1), 0), vscode.TextEditorRevealType.InCenter);
    }),
    vscode.commands.registerCommand("yanglabPdk.refreshCatalog", async () => {
      packageRoot = findPackageRoot(context.extensionPath);
      if (!packageRoot) return vscode.window.showErrorMessage("YanglabPDK package root was not found.");
      await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Refreshing YanglabPDK catalog" }, async () => {
        const python = await pythonPathFor(vscode.Uri.file(packageRoot));
        const script = path.join(packageRoot, "catalog", "generate_manifest.py");
        try {
          const result = await runProcess(python, [script], packageRoot);
          loaded = loadCatalog(context.extensionPath, packageRoot);
          tree.setComponents(loaded.data.components || []);
          vscode.window.showInformationMessage(result.stdout.trim() || "YanglabPDK catalog refreshed.");
        } catch (error) {
          vscode.window.showErrorMessage(`Catalog refresh failed: ${error.message}`);
        }
      });
    }),
    vscode.commands.registerCommand("yanglabPdk.regenerateThumbnails", async () => {
      packageRoot = findPackageRoot(context.extensionPath);
      if (!packageRoot) return vscode.window.showErrorMessage("YanglabPDK package root was not found.");
      await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Generating YanglabPDK thumbnails", cancellable: false }, async () => {
        const python = await pythonPathFor(vscode.Uri.file(packageRoot));
        const script = path.join(packageRoot, "catalog", "generate_thumbnails.py");
        try {
          const result = await runProcess(python, [script], packageRoot);
          loaded = loadCatalog(context.extensionPath, packageRoot);
          tree.setComponents(loaded.data.components || []);
          details.render();
          const lastLine = result.stdout.trim().split(/\r?\n/).at(-1);
          vscode.window.showInformationMessage(lastLine || "YanglabPDK thumbnails regenerated.");
        } catch (error) {
          vscode.window.showErrorMessage(`Thumbnail generation failed: ${error.message}`);
        }
      });
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate, buildSnippet, buildPlainCode };
