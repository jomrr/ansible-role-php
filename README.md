# Ansible Role: php

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-php)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-php)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-php)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-php/dev.yml?branch=dev&label=dev)](https://github.com/jomrr/ansible-role-php/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-php/main.yml?branch=main&label=main)](https://github.com/jomrr/ansible-role-php/actions/workflows/main.yml?query=branch%3Amain)

Install hardened PHP-FPM with application pools, explicit environments and
managed extensions.

## Purpose

Install and run the distribution PHP-FPM on AlmaLinux, Debian, Fedora,
openSUSE Leap, openSUSE Tumbleweed and Ubuntu. Configure a hardened baseline,
named application pools with explicit environments, and selected PHP or
Zend extensions. Reapplying unchanged input is idempotent.

## Scope

### Managed

- Distribution PHP-FPM and CLI packages, plus php_extra_packages.
- Global PHP settings, FPM master configuration and the authoritative list of
  application pools.
- Selected extension INI files, including explicit enabled and disabled states.
- Validated FPM reloads and an enabled, running service.

### Not Managed

- Application deployment, database credentials, web servers, TLS, system users
  and application-owned directories.
- Parallel PHP versions, third-party repositories and per-pool extension
  loading.
- SELinux or AppArmor policy changes for custom application paths or network
  access.

## Requirements

- Custom worker and socket users/groups must exist before applying the role.
- Custom chdir, chroot, socket parents, log and session/cache directories must
  exist with suitable ownership and MAC labels.

## Dependencies

```yaml
collections:
  - name: community.general
    version: '>=12.0.0'
```

## Role Variables

### `php_extra_packages`

Type: `list`. Required: `false`.

Additional native distribution packages providing application extensions.

Default:

```yaml
php_extra_packages: []
```

### `php_modules`

Type: `list`. Required: `false`.

Selected extension INI files; omitted modules remain unmanaged. Packages must be
installed through php_extra_packages.

Default:

```yaml
php_modules: []
```

### `php_ini_defaults`

Type: `dict`. Required: `false`.

PHP hardening baseline merged with php_ini_settings; string values use native
INI syntax.

Default:

```yaml
php_ini_defaults:
  expose_php: 'Off'
  display_errors: 'Off'
  display_startup_errors: 'Off'
  log_errors: 'On'
  allow_url_include: 'Off'
  cgi.fix_pathinfo: '0'
  opcache.validate_permission: '1'
  opcache.validate_root: '1'
  session.use_strict_mode: '1'
  session.use_only_cookies: '1'
  session.cookie_httponly: '1'
  session.cookie_secure: '1'
  session.cookie_samesite: Lax
```

### `php_ini_settings`

Type: `dict`. Required: `false`.

Overrides merged into php_ini_defaults; specify native INI values as strings.

Default:

```yaml
php_ini_settings: {}
```

### `php_fpm_pool_defaults`

Type: `dict`. Required: `false`.

Native pool baseline; platform worker/socket ownership, restricted sockets and
bounded dynamic workers.

Default:

```yaml
php_fpm_pool_defaults:
  listen.mode: '0660'
  listen.allowed_clients: 127.0.0.1,::1
  pm: dynamic
  pm.max_children: 10
  pm.start_servers: 2
  pm.min_spare_servers: 1
  pm.max_spare_servers: 3
  pm.max_requests: 500
  pm.process_idle_timeout: 10s
  process.dumpable: 'no'
  rlimit_core: '0'
  catch_workers_output: 'yes'
  clear_env: 'yes'
  security.limit_extensions: .php
  request_terminate_timeout: 120s
  php_admin_flag[log_errors]: 'on'
  php_admin_flag[display_errors]: 'off'
  php_admin_value[error_log]: /proc/self/fd/2
  php_admin_value[memory_limit]: 128M
```

### `php_fpm_pools`

Type: `list`. Required: `false`.

Authoritative nonempty list of pools; removed pools are deleted from the managed
subdirectory.

Default:

```yaml
php_fpm_pools:
  - name: www
```

### `php_fpm_global_settings`

Type: `dict`. Required: `false`.

Native global FPM overrides; the role owns include. Defaults preserve the
distribution PID and error log paths.

Default:

```yaml
php_fpm_global_settings: {}
```

## Managed Files

- `RedHat: /etc/php-fpm.conf, /etc/php-fpm.d/ansible/*.conf and selected files
  in /etc/php.d/.`
- `Debian/Ubuntu: /etc/php/<default-version>/fpm/php-fpm.conf,
  pool.d/ansible/*.conf and selected files in fpm/conf.d/.`
- `SUSE: /etc/php8/fpm/php-fpm.conf, /etc/php8/fpm/php-fpm.d/ansible/*.conf and
  selected files in /etc/php8/conf.d/.`
- `The PHP baseline is written to 99-ansible.ini in the platform scan
  directory.`

## Check Mode

Reports proposed changes to an already installed PHP-FPM without reloading the
service or changing module states.

- Initial check mode on a host without PHP is unsupported; Debian version
  discovery requires the installed php-fpm metapackage.
- Candidate native configuration validation runs on real writes, not during
  check mode.

## Service Behavior

Validates changed pool and master candidates, validates the assembled
configuration before reload, then enables and starts FPM.

### Handlers

- A single notification validates the complete configuration and reloads PHP-FPM
  after all files are updated.

## Security Notes

- Default pools use platform worker identities, local Unix sockets with mode
  0660, clear_env=yes, security.limit_extensions=.php, disabled core dumps and
  bounded worker counts and request duration.
- PHP hides its version and client-facing errors, logs errors, disables URL
  includes and path-info guessing, and uses strict cookie-only sessions with
  HttpOnly, Secure and SameSite=Lax.
- OPcache validates cached file permissions and chroot roots when the extension
  is installed.
- HTTPS is expected; HTTP-only deployments must explicitly set
  session.cookie_secure to '0'.
- Pool files, the master and PHP baseline are root-owned with mode 0600. Tasks
  rendering potentially secret settings hide output. Module INI files have mode
  0644 for compatibility with CLI; do not store secrets in module settings.
- Pools sharing a worker identity or filesystem permissions are not isolated
  tenants. Use separate accounts and private session, temporary and cache
  directories per application; an FPM pool is not a security sandbox.
- OPcache is shared across pools. Shared code using literal ini_get calls can
  observe another pool's cached settings (PHP issue 8699); use separate FPM
  instances when applications require stronger separation.
- Application PHP cannot undo php_admin_value or php_admin_flag settings. Native
  pool settings can override the role defaults explicitly.

## Operational Notes

- php_fpm_pools defaults to a single www pool. It is authoritative and must
  contain at least one entry. Removed pools are deleted only from the role-owned
  ansible subdirectory. Vendor and external pool files are retained but not
  included.
- Pool settings are a flat map of native FPM directives, including
  php_value[...], php_flag[...], php_admin_value[...] and php_admin_flag[...].
  Quote values such as 'on', 'off', 'yes', 'no', and '0660' in YAML.
- A pool's environment map emits env[NAME] entries with quoted values. Names
  must be shell-style identifiers; values must not contain double quotes or line
  breaks. FPM expands $NAME references from the master's environment.
- Pool settings override php_fpm_pool_defaults. With no listen override sockets
  are `/run/php-fpm/<name>.sock` on RPM platforms and `/run/php/<name>.sock` on
  Debian/Ubuntu. Default identities are apache:apache, www-data:www-data and
  wwwrun:www respectively.
- Module changes apply to the whole FPM process, not individual pools. RPM
  platforms share the extension scan directory with CLI; Debian manages FPM scan
  files independently and replaces selected symlinks without modifying their
  mods-available targets.
- Install extension packages explicitly using php_extra_packages. For bz2, use
  php-bz2 on Debian/Ubuntu and php8-bz2 on SUSE; RedHat includes bz2 in
  php-common. Package names differ for other extensions.
- Module filenames default to `20-<name>.ini` on RedHat/Debian and
  `10-<name>.ini` on SUSE. Set filename to the actual vendor basename when
  priorities differ (for example 10-opcache.ini). This prevents duplicate
  loading or an ineffective disable.
- Disabled modules retain an INI file with the loader line commented out.
  Omitted entries leave existing state untouched. Compiled-in modules cannot be
  disabled; the role verifies the selected states using php-fpm -m and fails on
  a mismatch.
- Since PHP 8.5, OPcache is built in. Configure opcache.enable through
  php_ini_settings rather than adding an opcache loader entry to php_modules. On
  older PHP versions, install the distribution's OPcache package when needed.
- PHP has no reliable native INI validator returning failure for every startup
  warning. Pool and master files use php-fpm -t -y; startup diagnostics from
  php-fpm -m fail the run, but arbitrary PHP INI values still require
  application validation. Package updates may reinstall vendor INI files;
  reapply the role afterward.
- Defaults log worker errors through FPM's captured stderr. Native slowlog and
  php_admin_value[error_log] settings can select application log files;
  provision their paths and log rotation separately. Function blacklists and
  open_basedir are not imposed.

## Supported Platforms

| OS Family | Distribution | Version | Container Image |
| --------- | ------------ | ------- | --------------- |
| RedHat | AlmaLinux | latest | [jomrr/molecule-almalinux:latest](https://hub.docker.com/r/jomrr/molecule-almalinux) |
| Debian | Debian | latest | [jomrr/molecule-debian:latest](https://hub.docker.com/r/jomrr/molecule-debian) |
| RedHat | Fedora | latest | [jomrr/molecule-fedora:latest](https://hub.docker.com/r/jomrr/molecule-fedora) |
| Suse | OpenSuse Leap | latest | [jomrr/molecule-opensuse-leap:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-leap) |
| Suse | OpenSuse Tumbleweed | latest | [jomrr/molecule-opensuse-tumbleweed:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-tumbleweed) |
| Debian | Ubuntu | latest | [jomrr/molecule-ubuntu:latest](https://hub.docker.com/r/jomrr/molecule-ubuntu) |

## Example Playbook

### Distribution PHP-FPM baseline

Starts a hardened www pool using the distribution worker identity
and a local Unix socket.

```yaml
- name: Configure PHP-FPM
  hosts: webservers
  gather_facts: true
  roles:
    - role: jomrr.php
```

### Kanboard and a separate www pool on Fedora

The nginx account and application, session, cache and log directories
are provisioned beforehand. This example uses native FPM directives.

```yaml

- name: Configure application PHP
  hosts: webservers
  gather_facts: true
  roles:
    - role: jomrr.php
      php_modules:
        - name: bz2
          state: enabled
        - name: ftp
          state: disabled
      php_fpm_pools:
        - name: www
        - name: kanboard
          settings:
            user: nginx
            group: nginx
            listen: /run/php-fpm/kanboard.sock
            listen.owner: nginx
            listen.group: nginx
            listen.mode: '0660'
            listen.backlog: 511
            pm: dynamic
            pm.max_children: 10
            pm.start_servers: 2
            pm.min_spare_servers: 1
            pm.max_spare_servers: 3
            chdir: /var/www/kanboard
            slowlog: /var/log/php-fpm/kanboard-slow.log
            request_slowlog_timeout: 5s
            php_admin_value[error_log]: /var/log/php-fpm/kanboard-error.log
            php_admin_value[memory_limit]: 128M
            php_value[session.save_handler]: files
            php_value[session.save_path]: /var/lib/php/kanboard/session
            php_value[soap.wsdl_cache_dir]: /var/lib/php/kanboard/wsdlcache
            php_value[opcache.file_cache]: /var/lib/php/kanboard/opcache
          environment:
            HOSTNAME: $HOSTNAME
            PATH: /usr/local/bin:/usr/bin:/bin
            TMP: /var/lib/php/kanboard/tmp
            TMPDIR: /var/lib/php/kanboard/tmp
            TEMP: /var/lib/php/kanboard/tmp
            APP_ENV: production
            DATABASE_URL: '{{ vault_kanboard_database_url }}'

```

## References

- [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php)
- [PHP INI scan directories](https://www.php.net/manual/en/configuration.file.php)
- [PHP 8.5 OPcache change](https://www.php.net/migration85.incompatible.php)
- [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php)
- [PHP shared-code INI cache issue](https://github.com/php/php-src/issues/8699)
- [PHP session security](https://www.php.net/manual/en/session.security.ini.php)

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
