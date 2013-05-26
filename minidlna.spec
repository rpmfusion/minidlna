Name:           minidlna
Version:        1.0.26
Release:        2%{?dist}
Summary:        Lightweight DLNA/UPnP-AV server targeted at embedded systems

Group:          System Environment/Daemons
License:        GPLv2 
URL:            http://sourceforge.net/projects/minidlna/
Source0:        http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
# Systemd unit file
Source1:        %{name}.service
# Debian man pages
Source2:        %{name}-1.0.24-debian-manpages.tar.gz
# tmpfiles.d configuration for the /var/run directory
Source3:        %{name}-tmpfiles.conf 

BuildRequires:  libuuid-devel
BuildRequires:  ffmpeg-devel
BuildRequires:  sqlite-devel
BuildRequires:  libvorbis-devel
BuildRequires:  flac-devel
BuildRequires:  libid3tag-devel
BuildRequires:  libjpeg-devel
BuildRequires:  libexif-devel
BuildRequires:  gettext
BuildRequires:  systemd-units
Requires(pre):  shadow-utils
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description
MiniDLNA (aka ReadyDLNA) is server software with the aim of being fully 
compliant with DLNA/UPnP-AV clients.

The minidlna daemon serves media files (music, pictures, and video) to 
clients on your network.  Example clients include applications such as 
Totem and XBMC, and devices such as portable media players, smartphones, 
and televisions.


%prep
%setup -q
%setup -D -T -q -a 2

# Honor RPM_OPT_FLAGS and include ffmpeg headers
sed -i 's!CFLAGS = -Wall -g -O3!CFLAGS += -I/usr/include/ffmpeg/!' Makefile

# Verbose Makefile
sed -i 's/@$(CC)/$(CC)/;s/&& exit 0\; \\//;/echo "The following command failed:/d' Makefile

# Edit the default config file to run the daemon with the minidlna user
sed -i 's/#db_dir=\/var\/cache\/minidlna/db_dir=\/var\/cache\/minidlna/' \
  %{name}.conf
sed -i 's/#log_dir=\/var\/log/log_dir=\/var\/log\/minidlna/' \
  %{name}.conf


%build
export CFLAGS="%{optflags}"
make %{?_smp_mflags} 

# Build language catalogs 
pushd po
for catsrc in *.po; do
    lang="${catsrc%.po}"
    msgfmt -o "$lang.mo" "$catsrc"
done
popd


%install
make install DESTDIR=%{buildroot}
make install-conf DESTDIR=%{buildroot}

# Install systemd unit file
mkdir -p %{buildroot}%{_unitdir}
install -m 644 %{SOURCE1} %{buildroot}%{_unitdir}

# Install man pages
mkdir -p %{buildroot}%{_mandir}/man1
install -m 644 debian-manpages/*.1 %{buildroot}%{_mandir}/man1/
mkdir -p %{buildroot}%{_mandir}/man5
install -m 644 debian-manpages/*.5 %{buildroot}%{_mandir}/man5/

# Install language catalogs
pushd po
for catalog in *.mo; do
    lang="${catalog%.mo}"
    install -d -m 0755 "%{buildroot}%{_datadir}/locale/${lang}/LC_MESSAGES"
    install -m 0644 "$catalog" "%{buildroot}%{_datadir}/locale/${lang}/LC_MESSAGES/minidlna.mo"
done
popd

# Install tmpfiles.d
mkdir -p %{buildroot}%{_sysconfdir}/tmpfiles.d
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf
mkdir -p %{buildroot}%{_localstatedir}/run/
install -d -m 0755 %{buildroot}%{_localstatedir}/run/%{name}/

# Create cache and log directories
mkdir -p %{buildroot}%{_localstatedir}/cache
install -d -m 0755 %{buildroot}%{_localstatedir}/cache/%{name}/
mkdir -p %{buildroot}%{_localstatedir}/log
install -d -m 0755 %{buildroot}%{_localstatedir}/log/%{name}/

%find_lang %{name}


%pre
getent group minidlna >/dev/null || groupadd -r minidlna
getent passwd minidlna >/dev/null || \
useradd -r -g minidlna -d /dev/null -s /sbin/nologin \
  -c "minidlna service account" minidlna
exit 0


%post
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi


%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi


%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi


%files -f %{name}.lang
%attr(-,minidlna,minidlna) %config(noreplace) %{_sysconfdir}/minidlna.conf
%{_sbindir}/minidlna
%{_unitdir}/minidlna.service
%{_mandir}/man1/%{name}.1*
%{_mandir}/man5/%{name}.conf.5*
%dir %attr(-,minidlna,minidlna) %{_localstatedir}/run/%{name}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%dir %attr(-,minidlna,minidlna) %{_localstatedir}/cache/%{name}/
%dir %attr(-,minidlna,minidlna) %{_localstatedir}/log/%{name}/
%doc LICENCE LICENCE.miniupnpd NEWS README TODO


%changelog
* Sun May 26 2013 Nicolas Chauvet <kwizart@gmail.com> - 1.0.26-2
- Rebuilt for x264/FFmpeg

* Wed May 08 2013 Andrea Musuruane <musuruan@gmail.com> - 1.0.26-1
- Updated to upstream 1.0.26

* Wed Jan 30 2013 Nicolas Chauvet <kwizart@gmail.com> - 1.0.25-4
- Rebuilt for ffmpeg

* Sat Nov 24 2012 Nicolas Chauvet <kwizart@gmail.com> - 1.0.25-3
- Rebuilt for FFmpeg 1.0

* Sat Nov 03 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.25-2
- Fixed FTBFS caused by ffmpeg 1.0
- Updated minidlna.service I forgot to commit (BZ #2294)

* Sat Jul 14 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.25-1
- Updated to upstream 1.0.25

* Tue Jun 26 2012 Nicolas Chauvet <kwizart@gmail.com> - 1.0.24-3
- Rebuilt for FFmpeg

* Wed Apr 25 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.24-2
- Run the daemon with the minidlna user (BZ #2294)
- Updated Debian man pages

* Sun Feb 19 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.24-1
- Updated to upstream 1.0.24

* Sat Jan 28 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.23-1
- Updated to upstream 1.0.23

* Sun Jan 22 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.22-2
- Fixed systemd unit file

* Sun Jan 15 2012 Andrea Musuruane <musuruan@gmail.com> 1.0.22-1
- Updated to upstream 1.0.22
- Removed default Fedora RPM features (defattr, BuildRoot, clean section)
- Better consistent macro usage

* Sat Jul 23 2011 Andrea Musuruane <musuruan@gmail.com> 1.0.21-1
- Updated to upstream 1.0.21

* Sat Jun 18 2011 Andrea Musuruane <musuruan@gmail.com> 1.0.20-1
- First release
- Used Debian man pages

