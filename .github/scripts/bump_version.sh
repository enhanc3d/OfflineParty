#!/bin/bash

# Read the current version from a version file (e.g., version.txt)
current_version=$(cat version.txt)

# Split the version into major, minor, and patch components
IFS='.' read -ra version_parts <<< "$current_version"
major="${version_parts[0]}"
minor="${version_parts[1]}"
patch="${version_parts[2]}"

# Choose the type of version bump (major, minor, or patch)
bump_type=$1

if [ "$bump_type" == "major" ]; then
  major=$((major + 1))
  minor=0
  patch=0
elif [ "$bump_type" == "minor" ]; then
  minor=$((minor + 1))
  patch=0
else
  patch=$((patch + 1))
fi

# Create the new version
new_version="$major.$minor.$patch"

# Update the version file with the new version
echo "$new_version" > version.txt

# Print the new version (for use in the GitHub Actions workflow)
echo "$new_version"
