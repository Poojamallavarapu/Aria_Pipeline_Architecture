py -0 - To check the installed versions

python --version (used to check the version)

If you have to change from an older version to Python 3.11 version, go to Ctrl+Shift+P, then you can choose Python 3.11 and select it in the interpreter.

```powershell
[Environment]::SetEnvironmentVariable("Path", "C:\Users\pooja\AppData\Local\Programs\Python\Python311;$([Environment]::GetEnvironmentVariable('Path', 'User'))", "User")
```

The next step is to set up ollama, so visit that
``` powershell
https://ollama.com/download 
```
## Open a new Command Prompt (CMD) and run:
```
where ollama
expected: C:\Users\pooja\AppData\Local\Programs\Ollama\ollama.exe
ollama --version
expected: ollama version 0.30.7
```

## Pull ollama models :

1)nomic-embed-text

2)llama3.1:8b






