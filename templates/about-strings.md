# About page strings

Add these in both languages. `res/values/strings.xml` holds the app's `default_language` from
`apps.yml`, and `res/values-<other>/strings.xml` holds the other one: `values-da/` for an app whose
default is English, `values-en/` for one whose default is Danish (guard-android). `check_inapp` looks
for that second folder.

| key | English | Danish |
|---|---|---|
| about_check_updates | Check for updates | Søg efter opdateringer |
| about_privacy_link | Read the privacy policy | Læs privatlivspolitikken |
| about_website | Open the website | Åbn hjemmesiden |
| about_source | See the source code on GitHub | Se kildekoden på GitHub |
| about_report | Report a problem on GitHub | Meld en fejl på GitHub |
| about_credits | Credits and licenses | Tak og licenser |
| about_made_by | Made by Cocode (cocode.dk) | Lavet af Cocode (cocode.dk) |

The section titles are the design's About-page sections in order: Name and version, What the app does, Privacy, Links, Credits and licenses, Made by Cocode, Support.
