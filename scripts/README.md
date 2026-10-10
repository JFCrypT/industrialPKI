# Scripts

The public workflow intentionally keeps automation minimal.

## Required / recommended

```text
generate_pki.sh
export_credentials.sh
bootstrap_raspberry_gateway.sh
```

These scripts cover the repetitive or error-prone tasks that benefit from automation:

- certificate/key generation;
- creation of deployment credential bundles;
- first-time Docker installation on the Raspberry Pi.

## Not required for understanding the project

The emulator, SCADA and Docker gateway can be started with the explicit commands documented in the main README.

Profile selection can also be performed directly:

```bash
cp .env.emulator .env
cp scada/scada_dual_config_emulator.json scada/scada_dual_config.json
```

or:

```bash
cp .env.physical .env
cp scada/scada_dual_config_physical.json scada/scada_dual_config.json
```

Helper scripts may exist during development, but they should not be presented as mandatory deployment steps.
