import shutil, time
from pathlib import Path
from common import run
SERVICES=["cyan-skillfish-governor-smu", "cyan-skillfish-governor"]
SERVICE=SERVICES[0]
APP=Path(__file__).resolve().parent.parent
OPT=APP/"configs"/"bc250-optimized-governor.toml"
CONF=Path("/etc/cyan-skillfish-governor-smu/config.toml")


def active_service():
    for svc in SERVICES:
        rc,msg=run(["systemctl","is-active",svc],5)
        if rc==0 or (msg or "").strip() in ("active","activating"):
            return svc
    for svc in SERVICES:
        rc,msg=run(["systemctl","is-enabled",svc],5)
        if rc==0 or (msg or "").strip()=="enabled":
            return svc
    return SERVICES[0]


def sudo_write(path, text):
    run(["sudo","install","-d","-m","0755",str(Path(path).parent)],30)
    import subprocess
    proc=subprocess.run(["sudo","tee",str(path)],input=text,text=True,capture_output=True,timeout=30)
    if proc.returncode!=0:
        raise PermissionError((proc.stderr or proc.stdout or f"tee rc={proc.returncode}").strip())

def install_config_from_opt():
    if not OPT.exists():
        return "", f"ERR optimized config missing: {OPT}"
    backup=""
    if CONF.exists():
        backup=str(CONF.with_suffix(f".toml.bak-{int(time.time())}")); run(["sudo","cp",str(CONF),backup],30)
    sudo_write(CONF, OPT.read_text())
    return backup, f"✓ optimized config installed: {CONF}"
def status():
    svc=active_service(); _,a=run(["systemctl","is-active",svc],5); _,e=run(["systemctl","is-enabled",svc],5)
    return {"service":svc,"active":a or "unknown","enabled":e or "unknown","config_exists":CONF.exists()}
def enable_copr_repo():
    """Enable Filippo R.'s Bazzite COPR repo so rpm-ostree can layer the latest build."""
    out = []
    repo_file = Path("/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:filippor:bazzite.repo")
    if repo_file.exists():
        out.append("✓ COPR already enabled: filippor/bazzite")
        return 0, "\n".join(out)

    if not shutil.which("dnf"):
        return 1, "ERR dnf is missing; cannot enable COPR filippor/bazzite automatically"

    rc, msg = run(["sudo", "dnf", "copr", "enable", "-y", "filippor/bazzite"], 180)
    if rc == 0:
        out.append("✓ COPR enabled: filippor/bazzite")
    else:
        out.append(msg or f"ERR dnf copr enable failed: {rc}")
    return rc, "\n".join(out)


def package_version():
    rc, msg = run(["rpm", "-q", SERVICE], 10)
    return msg.strip() if rc == 0 and msg else "not installed in current booted deployment"


def install():
    out=[]
    out.append("Checking COPR repository...")
    rc, msg = enable_copr_repo()
    out.append(msg)
    if rc != 0:
        return "\n".join(out + ["ERR could not enable COPR repository"])

    if shutil.which("rpm-ostree"):
        out.append("Layering latest cyan-skillfish-governor-smu with rpm-ostree...")
        commands = [
            ["sudo", "rpm-ostree", "install", "--idempotent", SERVICE],
            ["sudo", "rpm-ostree", "install", SERVICE],
        ]
        last = ""
        for c in commands:
            rc, msg = run(c, 600)
            last = msg or str(rc)
            lower = last.lower()
            if rc == 0 or "already requested" in lower or "already installed" in lower or "is already layered" in lower:
                out.append(last)
                out.append("✓ package deployed/requested through rpm-ostree")
                out.append("RESTART_REQUIRED=1")
                out.append("Restart required before the newly layered package is guaranteed active.")
                return "\n".join(out)
            if "unknown option" in lower or "unrecognized option" in lower:
                continue
            break
        return "\n".join(out + [last, "ERR rpm-ostree could not layer the governor package"])

    if shutil.which("dnf"):
        out.append("Installing latest cyan-skillfish-governor-smu with dnf...")
        rc,msg=run(["sudo","dnf","install","-y",SERVICE],600)
        out.append(msg or str(rc))
        if rc==0:
            out.append("✓ package installed")
            out.append(f"Version: {package_version()}")
            return "\n".join(out)

    return "\n".join(out+["ERR install failed: neither rpm-ostree nor dnf completed successfully"])
def enable_start():
    if not CONF.exists(): install_config_from_opt()
    o=[]
    for c in (["sudo","systemctl","enable",SERVICE],["sudo","systemctl","start",SERVICE]):
        rc,msg=run(c,30); o.append(msg or str(rc))
    return "\n".join(o)
def restart():
    svc=active_service(); rc,msg=run(["sudo","systemctl","restart",svc],30)
    return f"OK sudo systemctl restart {svc}" if rc==0 else (msg or f"ERR {rc}")
def logs():
    svc=active_service(); rc,msg=run(["journalctl","-u",svc,"-n","80","--no-pager"],20)
    return msg or f"ERR {rc}"
def optimize():
    backup,msg=install_config_from_opt()
    if msg.startswith("ERR"): return msg
    return f"OK optimized installed backup={backup} {restart()}"


def stop():
    svc=active_service(); rc, msg = run(["sudo", "systemctl", "stop", svc], 30)
    return f"OK sudo systemctl stop {svc}" if rc == 0 else (msg or f"ERR {rc}")


def deploy_one_click():
    """
    One-click Bazzite/Fedora deployment for the latest COPR governor.
    Enables filippor/bazzite COPR, layers/installs cyan-skillfish-governor-smu,
    installs the optimized BC-250 config, enables the service, and starts it when
    the current booted deployment already contains the service unit.
    """
    out = []
    out.append("🐟 One Click Deploy Governor")
    out.append("=" * 48)

    out.append("Step 1/5: Stop existing service if it is running")
    svc=active_service()
    rc, msg = run(["sudo", "systemctl", "stop", svc], 30)
    if rc == 0:
        out.append(f"✓ stopped existing service: {svc}")
    else:
        out.append(f"• stop skipped: {msg or rc}")

    out.append("")
    out.append("Step 2/5: Enable COPR and deploy latest package")
    install_msg = install()
    out.append(install_msg)
    install_low = install_msg.lower()
    reboot_required = "restart_required=1" in install_low
    if "err " in install_low or install_low.startswith("err"):
        return "\n".join(out)

    out.append("")
    out.append("Step 3/5: Install optimized BC-250 governor config")
    backup, cfgmsg = install_config_from_opt()
    if backup:
        out.append(f"✓ backup created: {backup}")
    out.append(cfgmsg)
    if cfgmsg.startswith("ERR"):
        return "\n".join(out)

    out.append("")
    out.append("Step 4/5: Enable governor service")
    svc=active_service()
    rc, msg = run(["sudo", "systemctl", "enable", svc], 30)
    if rc == 0:
        out.append(f"✓ enabled: {svc}")
    elif reboot_required:
        out.append("• service unit may appear only after restart on rpm-ostree systems")
    else:
        out.append(f"ERR enable failed: {msg or rc}")
        return "\n".join(out)

    out.append("")
    out.append("Step 5/5: Start governor service when available")
    rc, msg = run(["sudo", "systemctl", "start", svc], 30)
    if rc == 0:
        out.append(f"✓ started: {svc}")
    elif reboot_required:
        out.append("• start deferred until after restart because rpm-ostree layered the package into the next deployment")
    else:
        out.append(f"ERR start failed: {msg or rc}")
        return "\n".join(out)

    out.append("")
    out.append("Verification")
    rc, active = run(["systemctl", "is-active", svc], 10)
    rc2, enabled = run(["systemctl", "is-enabled", svc], 10)
    out.append(f"Service active: {active or 'pending restart'}")
    out.append(f"Service enabled: {enabled or 'pending restart'}")
    out.append(f"Package: {package_version()}")
    out.append(f"Config path: {CONF}")
    out.append("")
    out.append("✓ Governor deployment completed")
    if reboot_required:
        out.append("RESTART_REQUIRED=1")
        out.append("Restart now to boot into the deployment containing the latest governor.")
    else:
        out.append("No rpm-ostree restart marker was returned; governor should be usable now.")
    return "\n".join(out)
