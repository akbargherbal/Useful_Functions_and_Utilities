The reason your current script is returning generic names like `"Person 1"` and `"Person 2"` is that Chrome often leaves stale, default placeholder names inside the individual profile `Preferences` files.

The active display names and synced account names shown in the **"Who's using Chrome?"** UI are managed centrally in Chrome's global **`Local State`** configuration file.

You can extract the mapping directly from the global `Local State` file.

### PowerShell Script

Run the following script in your PowerShell terminal to query the central profile cache:

```powershell
$localStatePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Local State"

if (Test-Path $localStatePath) {
    $state = Get-Content -Raw -Path $localStatePath | ConvertFrom-Json
    $infoCache = $state.profile.info_cache

    if ($infoCache) {
        $infoCache.psobject.properties | ForEach-Object {
            $dirName = $_.Name
            $profileData = $_.Value

            [PSCustomObject]@{
                "Folder Name"   = $dirName
                "Profile Name"  = $profileData.name
                "Display Name"  = $profileData.gaia_name
                "Email / User"  = $profileData.user_name
                "Shortcut Name" = $profileData.shortcut_name
            }
        } | Format-Table -AutoSize
    } else {
        Write-Warning "Could not find profile info_cache in Local State."
    }
} else {
    Write-Error "Local State file not found at: $localStatePath"
}
```
