# YanglabPDK Explorer

Local VS Code component browser for YanglabPDK.

## Features

- Browse registered components by category.
- Search names, modules, and descriptions.
- Inspect signatures and edit parameters in the side bar.
- Insert a Python import plus a tab-navigable component snippet.
- Open the defining source file.
- Refresh the catalog using the selected Python interpreter.
- Show unregistered `@gf.cell` functions under **Unclassified**.

## Local setup

1. Open a workspace containing the `YanglabPDK` package.
2. Install the generated VSIX with **Extensions: Install from VSIX...**.
3. Open the YanglabPDK icon in the Activity Bar.
4. Optionally move the view to VS Code's Secondary Side Bar.

Set `yanglabPDK.packageRoot` if automatic workspace discovery cannot find the
package. Set `yanglabPDK.pythonPath` to override the active Python environment.

## Updating the catalog

Use the refresh icon in the Components view, or run:

```powershell
C:\Users\Jing\anaconda3\envs\Numerical\python.exe catalog\generate_manifest.py
```
