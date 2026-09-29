# Provenance

## Canonical accepted source

```text
pwnagotchi-final-20260926-201303.tar.gz
SHA-256: a183fae8ce88b7722878278cbd4c3ed83b0352f5c53ef0c7b0e9386a610cdfe9
```

The frozen manifest identified the accepted build-specific file set. The public repository tree is not a byte-for-byte copy of that archive because runtime/private material was deliberately removed and the remaining files were reorganized for publication.

## Sanitized documentation source

```text
pwnagotchi-final-20260926-201303-docsrc.tar.gz
SHA-256: 904b14a200d6df3d25fd5c0be6187af9f7c55e203f863f7fbd577a4fdeda231a
```

Sanitization removed the WPA-SEC SQLite runtime database, removed the private `config.toml`, generated an empty credential template, and removed runtime bytecode/log noise.

The original source archive hash and manifest are retained under `manifests/` for traceability.

## Upstream-derived source

The modified WPA-SEC and WiGLE plugin files are Pwnagotchi-derived GPL code. They are stored separately under `upstream/modified-plugins/` and covered by the third-party notices at the repository root.
