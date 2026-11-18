#!/usr/bin/python3
"""Exclude the inherited X11 locker only in this opt-in Plasma VM profile."""
import configparser,datetime,json,os,shutil,socket,subprocess
from pathlib import Path

def kde_only_exclusion(text):
    config=configparser.ConfigParser(interpolation=None,strict=False)
    config.optionxform=str;config.read_string(text)
    entry=config['Desktop Entry']
    values=[v for v in entry.get('NotShowIn','').split(';') if v]
    if 'KDE' not in values:values.append('KDE')
    entry['NotShowIn']=';'.join(values)+';'
    import io
    stream=io.StringIO();config.write(stream,space_around_delimiters=False)
    return stream.getvalue()

def empty_session():
    target=Path.home()/'.config/ksmserverrc'
    old=subprocess.check_output(['kreadconfig6','--file','ksmserverrc','--group','General','--key','loginMode'],text=True).strip()
    if old=='emptySession':return
    backup=Path.home()/'.local/state/steins-v4/session-restore'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup.mkdir(parents=True,mode=0o700)
    if target.exists():shutil.copy2(target,backup/'ksmserverrc')
    state=Path.home()/'.local/state/plasmasessionrestorestaterc'
    if state.exists():shutil.copy2(state,backup/state.name)
    (backup/'manifest.json').write_text(json.dumps({'target':str(target),'existed':target.exists(),'old_loginMode':old,'change':'emptySession for this disposable lab profile; saved session state retained'},indent=2)+'\n')
    subprocess.run(['kwriteconfig6','--file','ksmserverrc','--group','General','--key','loginMode','emptySession'],check=True)
    print('Selected an empty lab login; inherited review-session state backed up and retained.')

def main():
    assert os.getuid()==1000 and socket.gethostname()=='steins-prototype'
    assert subprocess.check_output(['systemd-detect-virt','--vm'],text=True).strip() in ('qemu','kvm')
    os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000')
    empty_session()
    # Confirm the maintained Plasma locker exists before excluding the X11-only one.
    subprocess.run(['gdbus','call','--session','--dest','org.freedesktop.ScreenSaver','--object-path','/ScreenSaver','--method','org.freedesktop.ScreenSaver.GetActive'],check=True)
    target=Path.home()/'.config/autostart/light-locker.desktop'
    upstream=Path('/etc/xdg/autostart/light-locker.desktop')
    if not upstream.is_file():print('Legacy locker absent; nothing to change');return
    source=target if target.exists() else upstream
    assert not source.is_symlink() and target.resolve().is_relative_to(Path.home())
    text=source.read_text();updated=kde_only_exclusion(text)
    if text==updated:print('KDE exclusion already present');return
    backup=Path.home()/'.local/state/steins-v4/legacy-locker'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup.mkdir(parents=True,mode=0o700)
    shutil.copy2(source,backup/'light-locker.desktop')
    (backup/'manifest.json').write_text(json.dumps({'target':str(target),'existed':target.exists(),'source':str(source),'change':'add KDE to NotShowIn; retain other desktops'},indent=2)+'\n')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(updated)
    print('Excluded legacy X11 locker in Plasma only; backed up to '+str(backup))

if __name__=='__main__':main()
