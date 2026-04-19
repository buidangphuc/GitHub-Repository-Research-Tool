if ! command -v uv &> /dev/null
then
    echo "uv could not be found. Please install uv first."
    exit
fi

echo "Syncing dependencies from pyproject.toml"
uv sync --dev
echo "uv environment setup completed."
