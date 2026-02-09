# GitHub Actions Setup Guide

## Supabase Connection Configuration

GitHub Actions requires IPv4 connectivity, but Supabase's direct database connection uses IPv6 by default. To resolve this, we use Supabase's **Supavisor connection pooler**, which provides IPv4 compatibility.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

### 1. Navigate to GitHub Secrets
Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### 2. Add the following secrets:

#### `TUSHARE_TOKEN`
Your Tushare API token for accessing Chinese stock market data.

#### `DB_HOST`
Your Supabase direct database host (used for extracting project reference).
- Format: `db.{project-ref}.supabase.co`
- Example: `db.abcdefghijklmnop.supabase.co`

#### `DB_POOLER_HOST`
Your Supabase connection pooler host (provides IPv4 compatibility).
- Format: `aws-0-{region}.pooler.supabase.com`
- Example: `aws-0-us-east-1.pooler.supabase.com`
- Find this in your Supabase Dashboard → Database → Connection Pooling

#### `DB_PORT`
Database port (usually `5432` for direct connection, but not used when pooler is enabled).
- Value: `5432`

#### `DB_NAME`
Database name.
- Value: `postgres` (default for Supabase)

#### `DB_USER`
Database user.
- Format: `postgres.{project-ref}` (for pooler) or `postgres` (for direct)
- Example: `postgres.abcdefghijklmnop`
- Note: The code automatically formats this for pooler connections

#### `DB_PASSWORD`
Your database password.
- Find this in your Supabase Dashboard → Database Settings → Database Password

## How to Find Your Supabase Connection Details

1. Go to your Supabase project dashboard
2. Navigate to `Settings` → `Database`
3. Under "Connection string", select "Connection pooling"
4. You'll see a connection string like:
   ```
   postgresql://postgres.{project}:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

From this connection string:
- `DB_POOLER_HOST` = `aws-0-us-east-1.pooler.supabase.com`
- `DB_USER` = `postgres` (the code will add the project reference automatically)
- `DB_PASSWORD` = Your password
- `DB_NAME` = `postgres`

## Connection Modes

The system supports two connection modes:

### Direct Connection (USE_POOLER=false)
- Uses IPv6 by default
- **Not recommended for GitHub Actions**
- Requires IPv4 add-on (paid feature) for IPv4 support

### Pooler Connection (USE_POOLER=true)
- Uses Supavisor connection pooler
- Provides IPv4 compatibility (free)
- **Recommended for GitHub Actions**
- Uses port 6543 (transaction mode)

## Troubleshooting

### Error: "Network is unreachable" with IPv6 address
This means the direct connection is being used. Ensure:
1. `USE_POOLER` is set to `true` in the workflow
2. `DB_POOLER_HOST` secret is configured correctly

### Error: "could not parse network address"
This was an issue in older versions where the code passed a hostname to the `hostaddr` parameter. This has been fixed in the latest version.

### Error: "SSL error: certificate verify failed"

This occurs when using `sslmode=verify-full` without the Supabase CA certificate. For GitHub Actions, use `sslmode=require` instead, which encrypts the connection but doesn't verify the certificate (acceptable for CI/CD environments).

## SSL Configuration

GitHub Actions workflows use `sslmode=require` which:

- Encrypts the connection to protect data in transit
- Does not verify the server certificate (acceptable for CI/CD)
- Does not require downloading the Supabase CA certificate

For local development with higher security requirements, you can use `sslmode=verify-full` by:

1. Downloading the Supabase CA certificate from your Database Settings
2. Setting the certificate path in your local environment

## References

- [Supabase IPv4/IPv6 Compatibility Guide](https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility-cHe3BP)
- [Supabase Database Connection Guide](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase SSL Enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement)
