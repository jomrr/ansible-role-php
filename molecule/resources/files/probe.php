<?php
// Read live values: OPcache can fold literal ini_get calls across shared pools (PHP #8699).
$settings = ini_get_all(null, false);
$temporary = tempnam(sys_get_temp_dir(), 'php-molecule-');
$temporaryDirectory = $temporary === false ? false : dirname($temporary);
if ($temporary !== false) {
    unlink($temporary);
}
$sessionWritten = false;
if (getenv('APP_ENV') === 'production') {
    session_start();
    $_SESSION['probe'] = 'managed-session';
    $sessionFile = session_save_path() . '/sess_' . session_id();
    session_write_close();
    $sessionWritten = is_file($sessionFile);
}
header('Content-Type: application/json');
echo json_encode([
    'environment' => getenv('APP_ENV'),
    'path' => getenv('PATH'),
    'inherited' => getenv('PHP_MOLECULE_UNLISTED'),
    'from_master' => getenv('FROM_MASTER'),
    'bz2' => extension_loaded('bz2'),
    'opcache_loaded' => extension_loaded('Zend OPcache'),
    'opcache_permissions' => $settings['opcache.validate_permission'] ?? false,
    'opcache_root' => $settings['opcache.validate_root'] ?? false,
    'memory_limit' => $settings['memory_limit'],
    'open_basedir' => $settings['open_basedir'],
    'sys_temp_dir' => $settings['sys_temp_dir'],
    'upload_tmp_dir' => $settings['upload_tmp_dir'],
    'temporary_directory' => $temporaryDirectory,
    'own_code_readable' => file_get_contents(__FILE__) !== false,
    'outside_readable' => @file_get_contents('/etc/hostname') !== false,

    'display_errors' => $settings['display_errors'],
    'expose_php' => $settings['expose_php'],
    'fix_pathinfo' => $settings['cgi.fix_pathinfo'],
    'session_written' => $sessionWritten,
    'session_path' => $settings['session.save_path'],
    'session_lifetime' => $settings['session.gc_maxlifetime'],
    'strict_session' => $settings['session.use_strict_mode'],
    'cookie_secure' => $settings['session.cookie_secure'],
    'cookie_httponly' => $settings['session.cookie_httponly'],
    'cookie_samesite' => $settings['session.cookie_samesite'],
]);
