{
  description = "A flake to handle skills development";

  # Add nixConfig to control what gets used in the flake
  nixConfig = {
    # Only allow these paths to be accessed by the builder
    allowed-uris = [
      "github:NixOS/nixpkgs"
      "github:numtide/devshell"
      "github:numtide/flake-utils"
    ];
    # Exclude everything but the flake.nix file from the build inputs
    flake-registry = "";
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    devshell.url = "github:numtide/devshell";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    devshell,
    flake-utils,
    nixpkgs,
    # nixpkgs-unstable
  }:
    flake-utils.lib.eachDefaultSystem (system: {
      devShells.default =
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [
              devshell.overlays.default
              # # When applied, the unstable nixpkgs set (declared in the flake inputs) will be accessible through 'pkgs.unstable'
              # (final: prev: {
              #   unstable = import nixpkgs-unstable {
              #     system = final.system;
              #     config = { allowUnfree = true; };
              #   };
              # })
              # (final: prev: {
              #   ansible = prev.python311.pkgs.ansible;
              #   ansible-lint = (prev.ansible-lint.override {
              #     python3 = prev.python311;
              #   });
              # })
            ];

            config = {
              allowUnfree = true;
            };
          };
        in
        pkgs.devshell.mkShell {
          name = "skills-devshell";
          # imports = [];
          # a list of packages to add to the shell environment
          packages = with pkgs; [
            graphviz
            mermaid-cli
          ];
          # imports = [ (devshell.importTOML ./devshell.toml) ];
        };
    });
}
