# sc docker login

After using this command you will be prompted for different options for your login.

- Registry to login:
 > This should include the base URL and relevant namespace. \
 > Example (GitHub): ghcr.io/organisation \
 > Example (Artifactory): your.artifactory.com/docker-registry
- Registry type: Currently the supported registry types are `github` or `artifactory`
- Use netrc?: Choose `y` to attempt to use credentials from your netrc or `n` for manual entry of credentials.
- Username/Api Key: This is only asked if you chose `n`, manually enter your username and api key for the registry
 > GitHub requires your username and Personal Access Token (see below for information on generating PAT) \
 > Artifactory requires your username and API key (see below for information on generating API key)


## Obtaining Credentials

### GitHub Container Registry (GHCR):

To create a Personal Access Token (PAT) for GitHub, follow the instructions [here.](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)

### Artifactory:

Currently, we use API Keys to access Artifactory. Find yours by:
- Clicking your profile icon in the top-right corner.
- Selecting Edit Profile.
- Scrolling down to API Key.

Note: Artifactory will transition to using Personal Access Tokens in Q4 2024. We will update this guide with the new instructions at that time.

## Example .netrc file

```
machine example.artifactory.com 
login <Your Username>
password <Your API Key> 

machine ghcr.io 
login  <Your Username>
password <Yout Personal Access Token>
```