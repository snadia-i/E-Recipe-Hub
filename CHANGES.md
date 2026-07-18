# Changes made

## UI preservation

- Restored the original user home, login, profile, recipe, collection, create/edit recipe, suspended-account, and administrator templates.
- Restored the original `styles.css`, sidebar icons, card layout, profile header, animated login backgrounds, and image assets.
- Kept the visual layout shown in the supplied screenshots.
- Added only invisible frontend support for CSRF tokens and corrected broken JavaScript references.

## Backend organisation

- Split routes into authentication, user, recipe, collection, and administrator modules.
- Split database operations into dedicated repositories.
- Centralised application configuration, SQLite connections, serializers, security helpers, and upload utilities.

## Database fixes

- Migrated the old collection structure to `collection` plus `collection_recipe`.
- Migrated legacy likes to the unique `recipe_like` relationship.
- Added missing report titles and recipe/collection timestamps where necessary.
- Preserved all original users, recipes, comments, collections, reports, and notifications.

## Security and permissions

- Added password hashing with automatic legacy-password upgrading.
- Added CSRF validation to forms and JavaScript requests.
- Added administrator checks and user ownership checks.
- Prevented users from editing or deleting recipes and comments they do not own.
- Stopped report sender IDs from being trusted from client-controlled URLs.
- Added image type validation, unique upload filenames, and a 5 MB upload limit.

## Functional fixes

- Fixed recipe creation when no image is selected.
- Fixed recipe editing without requiring the administrator API.
- Fixed recipe archive/unarchive and deletion actions.
- Fixed likes, comments, collection creation, saving, viewing, removal, and deletion.
- Fixed profile updates and password changes.
- Fixed filters, search, and sorting.
- Fixed administrator notification editing and report status updates.
- Fixed missing and incorrect JavaScript element IDs and API paths.
