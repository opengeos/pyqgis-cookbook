# Authentication infrastructure

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
  QgsApplication,
  QgsRasterLayer,
  QgsAuthMethodConfig,
  QgsDataSourceUri,
  QgsPkiBundle,
  QgsMessageLog,
)

from qgis.gui import (
    QgsAuthAuthoritiesEditor,
    QgsAuthConfigEditor,
    QgsAuthConfigSelect,
    QgsAuthSettingsWidget,
)

from qgis.PyQt.QtWidgets import (
    QWidget,
    QTabWidget,
)

from qgis.PyQt.QtNetwork import QSslCertificate
```

## Introduction

User reference of the Authentication infrastructure can be read
in the  User Manual in the *authentication_overview* paragraph.

This chapter describes the best practices to use the Authentication system from
a developer perspective.

The authentication system is widely used in QGIS Desktop by data providers whenever
credentials are required to access a particular resource, for example when a layer
establishes a connection to a Postgres database.

There are also a few widgets in the QGIS gui library that plugin developers can use to
easily integrate the authentication infrastructure into their code:

* `QgsAuthConfigEditor `
* `QgsAuthConfigSelect `
* `QgsAuthSettingsWidget `

A good code reference can be read from the authentication infrastructure
[tests code ](tests/src/python/test_qgsauthsystem.py).

**Warning:**  Due to the security constraints that were taken into account during the authentication  infrastructure design, only a selected subset of the internal methods are exposed to Python.

## Glossary

Here are some definition of the most common objects treated in this chapter.

## QgsAuthManager the entry point

The `QgsAuthManager ` singleton
is the entry point to use the credentials stored in the QGIS encrypted
:term:`Authentication DB`, i.e. the `qgis-auth.db` file under the
active *user profile <user_profiles>* folder.

This class takes care of the user interaction: by asking to set a master
password or by transparently using it to access encrypted stored information.

### Init the manager and set the master password

The following snippet gives an example to set master password to open the
access to the authentication settings. Code comments are important to
understand the snippet.

```python
authMgr = QgsApplication.authManager()

# check if QgsAuthManager has already been initialized... a side effect
# of the QgsAuthManager.init() is that AuthDbPath is set.
# QgsAuthManager.init() is executed during QGIS application init and hence
# you do not normally need to call it directly.
if authMgr.authenticationDatabasePath():
    # already initialized => we are inside a QGIS app.
    if authMgr.masterPasswordIsSet():
        msg = 'Authentication master password not recognized'
        assert authMgr.masterPasswordSame("your master password"), msg
    else:
        msg = 'Master password could not be set'
        # The verify parameter checks if the hash of the password was
        # already saved in the authentication db
        assert authMgr.setMasterPassword("your master password",
                                          verify=True), msg
else:
    # outside qgis, e.g. in a testing environment => setup env var before
    # db init
    os.environ['QGIS_AUTH_DB_DIR_PATH'] = "/path/where/located/qgis-auth.db"
    msg = 'Master password could not be set'
    assert authMgr.setMasterPassword("your master password", True), msg
    authMgr.init("/path/where/located/qgis-auth.db")
```

### Populate authdb with a new Authentication Configuration entry

Any stored credential is a :term:`Authentication Configuration` instance of the
`QgsAuthMethodConfig `
class accessed using a unique string like the following one:

```python
authcfg = 'fm1s770'
```

that string is generated automatically when creating an entry using the QGIS API or
GUI, but it might be useful to manually set it to a known value in case the
configuration must be shared (with different credentials) between multiple users within
an organization.

`QgsAuthMethodConfig ` is the base class
for any :term:`Authentication Method`.
Any Authentication Method sets a configuration hash map where authentication
information will be stored. Hereafter a useful snippet to store PKI-path
credentials for a hypothetical alice user:

```python
authMgr = QgsApplication.authManager()
# set alice PKI data
config = QgsAuthMethodConfig()
config.setName("alice")
config.setMethod("PKI-Paths")
config.setUri("https://example.com")
config.setConfig("certpath", "path/to/alice-cert.pem" )
config.setConfig("keypath", "path/to/alice-key.pem" )
# check if method parameters are correctly set
assert config.isValid()

# register alice data in authdb returning the ``authcfg`` of the stored
# configuration
authMgr.storeAuthenticationConfig(config)
newAuthCfgId = config.id()
assert newAuthCfgId
```

Available Authentication methods
................................

:term:`Authentication Method` libraries are loaded dynamically during
authentication manager init. Available authentication methods are:

.. list-table::
   :header-rows: 1
   :widths: auto
   :class: longtable

   * - Method
     - Description
     - Target providers
   * - `Basic`
     - User and password authentication
     - postgres, oracle, ows, wfs, wcs, wms, ogr, gdal, proxy
   * - `APIHeader`
     - HTTP headers
     - ows, wfs, wcs, wms
   * - `AWSS3`
     - AWS Simple Storage Service
     - awss3
   * - `EsriToken`
     - ESRI token based authentication for ArcGIS REST servers
     - arcgismapserver, arcgisfeatureserver
   * - `Identity-Cert`
     - Identity certificate authentication
     - ows, wfs, wcs, wms, postgres
   * - `MapTilerHmacSha256`
     - MapTiler HMAC-SHA256
     - wms, vectortile, xyzvectortiles
   * - `OAuth2`
     - OAuth2 authentication
     - ows, wfs, wcs, wms
   * - `PKI-Paths`
     - PKI paths authentication
     - ows, wfs, wcs, wms, postgres
   * - `PKI-PKCS#12`
     - PKI PKCS#12 authentication
     - ows, wfs, wcs, wms, postgres
   * - `PlanetaryComputer`
     - Microsoft Planetary Computer authentication
     - gdal, copc, stac

Populate Authorities
....................

```python
authMgr = QgsApplication.authManager()
# add authorities
cacerts = QSslCertificate.fromPath( "/path/to/ca_chains.pem" )
assert cacerts is not None
# store CA
authMgr.storeCertAuthorities(cacerts)
# and rebuild CA caches
authMgr.rebuildCaCertsCache()
authMgr.rebuildTrustedCaCertsCache()
```

Manage PKI bundles with QgsPkiBundle
....................................

A convenience class to pack PKI bundles composed on SslCert, SslKey and CA
chain is the `QgsPkiBundle `
class. Hereafter a snippet to get password protected:

```python
# add alice cert in case of key with pwd
caBundlesList = []  # List of CA bundles
bundle = QgsPkiBundle.fromPemPaths( "/path/to/alice-cert.pem",
                                     "/path/to/alice-key_w-pass.pem",
                                     "unlock_pwd",
                                     caBundlesList )
assert bundle is not None
# You can check bundle validity by calling:
# bundle.isValid()
```

Refer to `QgsPkiBundle ` class documentation
to extract cert/key/CAs from the bundle.

### Remove an entry from authdb

We can remove an entry from :term:`Authentication Database` using it's
`authcfg` identifier with the following snippet:

```python
authMgr = QgsApplication.authManager()
authMgr.removeAuthenticationConfig( "authCfg_Id_to_remove" )
```

### Leave authcfg expansion to QgsAuthManager

The best way to use an :term:`Authentication Config` stored in the
:term:`Authentication DB` is referring it with the unique identifier
`authcfg`. Expanding, means convert it from an identifier to a complete
set of credentials.
The best practice to use stored :term:`Authentication Config`\s, is to leave it
managed automatically by the Authentication manager.
The common use of a stored configuration is to connect to an authentication
enabled service like a WMS or WFS or to a DB connection.

**Note:** ake into account that not all QGIS data providers are integrated with the uthentication infrastructure. Each authentication method, derived from the ase class :class:`QgsAuthMethod <qgis.core.QgsAuthMethod>` nd support a different set of Providers. For example the :meth:`certIdentity() qgis.core.QgsAuthManager.certIdentity>` method supports the following list f providers: ample output: . testoutput:: auth   ['ows', 'wfs', 'wcs', 'wms', 'postgres']

```python
authM = QgsApplication.authManager()
print(authM.authMethod("Identity-Cert").supportedDataProviders())
```

For example, to access a WMS service using stored credentials identified with
`authcfg = 'fm1s770'`, we just have to use the `authcfg` in the data source
URL like in the following snippet:

```python
authCfg = 'fm1s770'
quri = QgsDataSourceUri()
quri.setParam("layers", 'usa:states')
quri.setParam("styles", '')
quri.setParam("format", 'image/png')
quri.setParam("crs", 'EPSG:4326')
quri.setParam("dpiMode", '7')
quri.setParam("featureCount", '10')
quri.setParam("authcfg", authCfg)   # <---- here my authCfg url parameter
quri.setParam("contextualWMSLegend", '0')
quri.setParam("url", 'https://my_auth_enabled_server_ip/wms')
rlayer = QgsRasterLayer(str(quri.encodedUri(), "utf-8"), 'states', 'wms')
```

In the upper case, the `wms` provider will take care to expand `authcfg`
URI parameter with credential just before setting the HTTP connection.

**Warning:** he developer would have to leave ``authcfg`` expansion to the :class:`QgsAuthManager qgis.core.QgsAuthManager>`, in this way he will be sure that expansion is not done too early.

Usually an URI string, built using the `QgsDataSourceURI `
class, is used to set a data source in the following way:

```python
authCfg = 'fm1s770'
quri = QgsDataSourceUri("my WMS uri here")
quri.setParam("authcfg", authCfg)
rlayer = QgsRasterLayer( quri.uri(False), 'states', 'wms')
```

**Note:** he ``False`` parameter is important to avoid URI complete expansion of the `authcfg`` id present in the URI.

PKI examples with other data providers
......................................

Other example can be read directly in the QGIS tests upstream as in
[test_authmanager_pki_ows ](tests/src/python/test_authmanager_pki_ows.py) or
[test_authmanager_pki_postgres ](tests/src/python/test_authmanager_pki_postgres.py).

## Adapt plugins to use Authentication infrastructure

Many third party plugins are using httplib2 or other Python networking libraries to manage HTTP
connections instead of integrating with `QgsNetworkAccessManager `
and its related Authentication Infrastructure integration.

To facilitate this integration a helper Python function has been created
called `NetworkAccessManager`. Its code can be found `here
<https://github.com/rduivenvoorde/pdokservicesplugin/blob/master/networkaccessmanager.py>`_.

This helper class can be used as in the following snippet:

```python
http = NetworkAccessManager(authid="my_authCfg", exception_class=My_FailedRequestError)
try:
  response, content = http.request( "my_rest_url" )
except My_FailedRequestError, e:
  # Handle exception
  pass
```

## Authentication GUIs

In this paragraph are listed the available GUIs useful to integrate
authentication infrastructure in custom interfaces.

### GUI to select credentials

If it's necessary to select a :term:`Authentication Configuration` from the set
stored in the :term:`Authentication DB` it is available in the GUI class
`QgsAuthConfigSelect `.

![](img/QgsAuthConfigSelect.png)

and can be used as in the following snippet:

```python
# create the instance of the QgsAuthConfigSelect GUI hierarchically linked to
# the widget referred with `parent`
parent = QWidget()  # Your GUI parent widget
gui = QgsAuthConfigSelect( parent, "postgres" )
# add the above created gui in a new tab of the interface where the
# GUI has to be integrated
tabGui = QTabWidget()
tabGui.insertTab( 1, gui, "Configurations" )
```

The above example is taken from the QGIS source :source:`code
<src/providers/postgres/qgspgnewconnection.cpp#L42>`.
The second parameter of the GUI constructor refers to data provider type. The
parameter is used to restrict the compatible :term:`Authentication Method`\s with
the specified provider.

### Authentication Editor GUI

The complete GUI used to manage credentials, authorities and to access to
Authentication utilities is managed by the
`QgsAuthEditorWidgets ` class.

![](img/QgsAuthEditorWidgets.png)

and can be used as in the following snippet:

```python
# create the instance of the QgsAuthEditorWidgets GUI hierarchically linked to
# the widget referred with `parent`
parent = QWidget()  # Your GUI parent widget
gui = QgsAuthConfigSelect( parent )
gui.show()
```

An integrated example can be found in the related :source:`test
<tests/src/python/test_qgsauthsystem.py#L80>`.

### Authorities Editor GUI

A GUI used to manage only authorities is managed by the
`QgsAuthAuthoritiesEditor ` class.

![](img/QgsAuthAuthoritiesEditor.png)

and can be used as in the following snippet:

```python
# create the instance of the QgsAuthAuthoritiesEditor GUI hierarchically
#  linked to the widget referred with `parent`
parent = QWidget()  # Your GUI parent widget
gui = QgsAuthAuthoritiesEditor( parent )
gui.show()
```