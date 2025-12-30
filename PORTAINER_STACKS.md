# Portainer Stack File Management

## Overview

This project uses a **template-based approach** to generate deployment-specific Portainer stack files. This eliminates duplication and reduces configuration errors when deploying to different environments.

## Files

- **`portainer-stack.template.yml`** - Single source of truth template (DO NOT deploy this directly)
- **`generate-portainer-stacks.sh`** - Script to generate deployment-specific files
- **`portainer-stack.yml`** - Default home lab stack (PUB_SOURCE=Mu)
- **`portainer-stack-rosa.yml`** - Stack for ROSA host (home lab)
- **`portainer-stack-twix.yml`** - Stack for TWIX host (home lab)
- **`portainer-stack-vultr2.yml`** - Stack for Vultr VM deployment (host networking)

## Quick Start

### Generate All Standard Stack Files
```bash
./generate-portainer-stacks.sh --all    # Generates ROSA, TWIX, and VULTR2
```

### Generate Specific Stacks
```bash
./generate-portainer-stacks.sh --ROSA --TWIX    # Generate ROSA and TWIX only
./generate-portainer-stacks.sh --VULTR2         # Generate Vultr VM only
./generate-portainer-stacks.sh --home-lab       # Generate default home lab
```

### Generate Custom Stack
```bash
./generate-portainer-stacks.sh --pub_source=MyHost  # Creates portainer-stack-myhost.yml
```

## Command Options

The generation script supports the following options:

- `--home-lab` - Generate default home lab stack with PUB_SOURCE=Mu
- `--ROSA` - Generate stack for ROSA host (bridge networking)
- `--TWIX` - Generate stack for TWIX host (bridge networking)
- `--VULTR2` - Generate stack for VULTR2 VM (host networking)
- `--pub_source=VALUE` - Generate custom stack with specified PUB_SOURCE
- `--all` - Generate all standard stacks (ROSA, TWIX, VULTR2)
- `--help` / `-h` - Display help message

**Multiple options can be specified in a single command.**

## Workflow

### 1. Making Changes

**IMPORTANT:** Only edit the template file, never edit the generated files directly!

```bash
# Edit the template
vi portainer-stack.template.yml

# Regenerate the deployment files
./generate-portainer-stacks.sh

# Commit both template and generated files
git add portainer-stack.template.yml portainer-stack*.yml
git commit -m "Update stack configuration"
```

### 2. Deploying to Portainer

1. Run the generation script
2. Copy the content of the appropriate generated file:
   - **Home Lab (ROSA/TWIX)**: Use `portainer-stack.yml`
   - **Vultr VM**: Use `portainer-stack-vultr2.yml`
3. In Portainer: **Stacks** → **Add Stack** → **Web Editor**
4. Paste the content and deploy

## Key Differences Between Deployments

| Aspect                  | Home Lab (ROSA/TWIX)                                      | Vultr VM (VULTR2)            |
| ----------------------- | --------------------------------------------------------- | ---------------------------- |
| **Files**               | `portainer-stack-rosa.yml`<br/>`portainer-stack-twix.yml` | `portainer-stack-vultr2.yml` |
| **Network Mode**        | Bridge                                                    | Host                         |
| **PUB_SOURCE**          | ROSA or TWIX                                              | VULTR2                       |
| **DEPLOYMENT_SCENARIO** | home-lab                                                  | vultr-vm                     |
| **MQTT Broker**         | Remote (n-vultr2)                                         | Localhost                    |

## Usage Examples

```bash
# Generate all three standard stacks
./generate-portainer-stacks.sh --all

# Generate only ROSA and TWIX for home lab testing
./generate-portainer-stacks.sh --ROSA --TWIX

# Generate custom stack for a new host
./generate-portainer-stacks.sh --pub_source=NewHost

# Multiple custom stacks
./generate-portainer-stacks.sh --pub_source=Host1 --pub_source=Host2
```, you have two options:

### Option 1: Use Custom PUB_SOURCE (Recommended for one-off deployments)
```bash
./generate-portainer-stacks.sh --pub_source=NewHostName
```

This creates `portainer-stack-newhostname.yml` with bridge networking.

### Option 2: Add New Hardcoded Host (For permanent deployments)

1. Edit `generate-portainer-stacks.sh`
2. Add a new case to handle your host in the main() function:
   ```bash
   --NEWHOST)
       targets+=("NEWHOST")
       ;;
   ```
3. Add corresponding case in the target processing loop:
   ```bash
   NEWHOST)
       generate_stack "NEWHOST" "bridge" "${SCRIPT_DIR}/portainer-stack-newhost.yml"
       ;;
   ```
4. Update usage() function with the new option
5. Test: `./generate-portainer-stacks.sh --NEWHOSTon (bridge vs host)
- `{{NETWORK_CONFIG_COMMENT}}` - Comments explaining network setup
- `{{DEPLOYMENT_SCENARIO}}` - Deployment scenario name
- `{{PUB_SOURCE}}` - Publisher source identifier
- `{{PUB_SOURCE_EXAMPLES}}` - Example commented PUB_SOURCE values
- `{{BROKER_NAME}}` - MQTT broker configuration name
- `{{DEPLOYMENT_COMMENT}}` - Deployment-specific comments

## Adding New Deployments

To add a new deployment type (e.g., for a new host):

1. Edit `generate-portainer-stacks.sh`
2. Add a new `generate_xxx()` function
3. Define the specific configuration values
4. Add the new target to the `main()` function
5. Test: `./generate-portainer-stacks.sh xxx`

## Validation

The script performs basic validation:
- Checks if template file exists
- Provides colored output for success/errors
- Shows clear error messages

## Best Practices

### ✅ DO
- Edit only the template file
- Run the generation script after template changes
- Commit both template and generated files to git
- Review generated files before deploying

### ❌ DON'T
- Don't edit `portainer-stack.yml` or `portainer-stack-vultr2.yml` directly
- Don't deploy `portainer-stack.template.yml` directly to Portainer
- Don't manually sync changes between files

## Troubleshooting

### "Template file not found"
```bash
# Ensure you're in the project root directory
cd /path/to/Weather_Sensors_and_Smartplugs_with_MQTT
./generate-portainer-stacks.sh
```

### Generated files have wrong permissions
```bash
chmod +x generate-portainer-stacks.sh
```

### Changes not appearing in generated files
```bash
# Ensure template was saved
# Regenerate files
./generate-portainer-stacks.sh

# Check diff
diff portainer-stack.template.yml portainer-stack.yml
```

## Migration from Old Workflow

If you previously had separate files that you edited manually:

1. Review both existing files
2. Update the template with any custom changes
3. Regenerate: `./generate-portainer-stacks.sh`
4. Compare: Ensure generated files match your requirements
5. Going forward: Only edit the template

## Version Control

Recommended `.gitignore` patterns:
```
# Keep template and script
# Keep generated files (for reference)
# All files are committed
```

For CI/CD workflows, you can generate files during deployment:
```bash
# In your deployment pipeline
./generate-portainer-stacks.sh vultr-vm
# Deploy portainer-stack-vultr2.yml
```
