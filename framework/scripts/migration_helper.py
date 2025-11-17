import argparse
import os
from datetime import datetime

def generate_properties(primitive_type: str, name: str, category: str | None = None) -> str:
    """Generates the universal and type-specific properties for a Logseq page."""
    properties = [
        f'type:: {primitive_type}',
        'status:: stable',
        'tags:: #migration-v2',
        'context-level:: 3-Technical',
        f'created-date:: [[{datetime.now().strftime("%Y-%m-%d")}]]',
        f'last-updated:: [[{datetime.now().strftime("%Y-%m-%d")}]]',
        'migrated:: true',
        f'migration-date:: [[{datetime.now().strftime("%Y-%m-%d")}]]',
        'migration-version:: 2.0'
    ]

    if primitive_type == '[C] CoreConcept':
        properties.extend([
            'summary:: [One-sentence definition]',
            'implemented-by::',
            'related-concepts::',
            'documentation::',
            'examples::'
        ])
    elif primitive_type == '[P] Primitive':
        _category = category.lower() if category else '[category]'
        properties.extend([
            f'import-path:: from tta_dev_primitives.{_category} import {name}',
            'source-file:: packages/tta-dev-primitives/src/...',
            f'category:: {_category}',
            'input-type:: [type annotation]',
            'output-type:: [type annotation]',
            'composes-with::',
            'uses-data::',
            'observability-spans::',
            'test-coverage:: 100%',
            'example-files::'
        ])
    elif primitive_type == '[D] DataSchema':
        properties.extend([
            'source-file:: packages/tta-dev-primitives/src/...',
            'base-class:: BaseModel | TypedDict | dataclass',
            'used-by::',
            'fields::',
            'validation::'
        ])
    elif primitive_type == '[I] Integration':
        _category = category.lower() if category else '[category]'
        properties.extend([
            'integration-type:: mcp | llm | database | code-execution | tool',
            'external-service:: [service name]',
            'wraps-primitive::',
            'requires-config::',
            'api-endpoint:: [URL]',
            'dependencies::',
            f'import-path:: from tta_dev_primitives.integrations.{_category} import {name}',
            'source-file:: packages/tta-dev-primitives/src/...'
        ])
    elif primitive_type == '[S] Service':
        properties.extend([
            'service-type:: infrastructure | observability | api | database | cache',
            'deployment:: docker | systemd | cloud | embedded',
            'exposes::',
            'depends-on::',
            'configuration::',
            'monitoring::'
        ])
    return '\n'.join(properties)

def generate_new_filename(primitive_type: str, original_name: str, category: str | None = None) -> str:
    """Generates the new namespaced filename."""
    if primitive_type == '[C] CoreConcept':
        return f'TTA.dev_Concepts_{original_name}.md'
    elif primitive_type == '[P] Primitive':
        return f'TTA.dev_Primitives_{category}_{original_name}.md'
    elif primitive_type == '[D] DataSchema':
        return f'TTA.dev_Data_{original_name}.md'
    elif primitive_type == '[I] Integration':
        return f'TTA.dev_Integrations_{category}_{original_name}.md'
    elif primitive_type == '[S] Service':
        return f'TTA.dev_Services_{original_name}.md'
    return f'{original_name}.md' # Fallback

def main():
    parser = argparse.ArgumentParser(description="Generate migration properties and new filename for Logseq pages.")
    parser.add_argument('--page', required=True, help='Original Logseq page name (e.g., "WorkflowContext").')
    parser.add_argument('--type', required=True, choices=['[C] CoreConcept', '[P] Primitive', '[D] DataSchema', '[I] Integration', '[S] Service'],
                        help='New primitive type ([C], [P], [D], [I], or [S]).')
    parser.add_argument('--category', help='Category for Primitives or Integrations (e.g., "Recovery", "CodeExecution"). Required for [P] and [I] types.')

    args = parser.parse_args()

    if args.type in ['[P] Primitive', '[I] Integration'] and not args.category:
        parser.error("--category is required for Primitive and Integration types.")

    original_name = args.page
    primitive_type = args.type
    category = args.category

    new_filename = generate_new_filename(primitive_type, original_name, category)
    properties = generate_properties(primitive_type, original_name, category)

    print(f"--- Generated for page: {original_name} ---")
    print(f"\nNew Filename: {new_filename}")
    print("\n--- Properties to add ---")
    print(properties)
    print("\n-------------------------")

if __name__ == "__main__":
    main()
