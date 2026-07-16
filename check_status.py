from pathlib import Path
b = Path(r"b:\Documents\GitHub\Command Nexus")
r = []
r.append(f"exe: {(b / 'dist' / 'HermesPressureTester.exe').exists()}")
r.append(f"spec: {(b / 'HermesPressureTester.spec').exists()}")
r.append(f"build_dir: {(b / 'build' / 'HermesPressureTester').exists()}")
d = Path.home() / "Desktop" / "HermesPressureTester.exe"
r.append(f"desktop: {d.exists()}")
if (b / 'dist' / 'HermesPressureTester.exe').exists():
    r.append(f"size: {(b / 'dist' / 'HermesPressureTester.exe').stat().st_size / 1024 / 1024:.1f} MB")
(b / 'status.txt').write_text("\n".join(r))
