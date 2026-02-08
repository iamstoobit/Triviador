from __future__ import annotations
from typing import List, Dict, Any
import json
from pathlib import Path


class CategoryManager:
    """
    Manages question categories and their relationships.
    """

    def __init__(self, config_path: str = "data/categories.json"):
        """
        Initialize category manager.

        Args:
            config_path: Path to categories configuration file
        """
        self.config_path = config_path
        self.categories: List[str] = []
        self.category_groups: Dict[str, List[str]] = {}
        self._load_categories()

    def _load_categories(self) -> None:
        """Load categories from configuration file."""
        path = Path(self.config_path)

        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    # Simple list of categories
                    self.categories = data
                elif isinstance(data, dict):
                    # Complex structure with groups
                    if 'categories' in data:
                        self.categories = data['categories']
                    if 'groups' in data:
                        self.category_groups = data['groups']
            except (json.JSONDecodeError, IOError):
                self._create_default_categories()
        else:
            self._create_default_categories()
            self._save_categories()

    def _create_default_categories(self) -> None:
        """Create default categories."""
        self.categories = [
            "Geography",
            "History",
            "Science",
            "Entertainment",
            "Sports",
            "Art",
            "Literature",
            "Technology",
            "Movies",
            "Music",
            "General Knowledge",
            "Pop Culture"
        ]

        # Define some logical groups
        self.category_groups = {
            "Academic": ["Geography", "History", "Science", "Art", "Literature"],
            "Entertainment": ["Entertainment", "Movies", "Music", "Pop Culture"],
            "Modern": ["Technology", "Pop Culture", "Entertainment"],
            "Classic": ["Geography", "History", "Science", "Art", "Literature"]
        }

    def _save_categories(self) -> None:
        """Save categories to configuration file."""
        data: Dict[str, Any] = {
            'categories': self.categories,
            'groups': self.category_groups
        }

        Path(self.config_path).parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        return self.categories.copy()

    def validate_categories(self, selected_categories: List[str]) -> List[str]:
        """
        Validate and filter selected categories.

        Args:
            selected_categories: List of categories to validate

        Returns:
            Validated list of categories (only those that exist)
        """
        valid_categories = set(self.categories)
        return [cat for cat in selected_categories if cat in valid_categories]

    def get_category_group(self, group_name: str) -> List[str]:
        """
        Get categories in a specific group.

        Args:
            group_name: Name of the group

        Returns:
            List of categories in the group, or empty list if group doesn't exist
        """
        return self.category_groups.get(group_name, []).copy()

    def add_category(self, category: str) -> bool:
        """
        Add a new category.

        Args:
            category: Name of category to add

        Returns:
            True if added, False if already exists
        """
        if category not in self.categories:
            self.categories.append(category)
            self.categories.sort()
            self._save_categories()
            return True
        return False

    def remove_category(self, category: str) -> bool:
        """
        Remove a category.

        Args:
            category: Name of category to remove

        Returns:
            True if removed, False if not found
        """
        if category in self.categories:
            self.categories.remove(category)

            # Remove from all groups
            for group_categories in self.category_groups.values():
                if category in group_categories:
                    group_categories.remove(category)

            self._save_categories()
            return True
        return False

    def get_filtered_categories(self, mode: str, selected: List[str]) -> List[str]:
        """
        Get filtered categories based on inclusion/exclusion mode.

        Args:
            mode: "include" or "exclude"
            selected: Selected categories

        Returns:
            List of categories to use
        """
        if mode == "include":
            return self.validate_categories(selected)
        elif mode == "exclude":
            all_cats = set(self.categories)
            excluded = set(selected)
            included = all_cats - excluded
            return sorted(list(included))
        else:
            return self.categories.copy()


if __name__ == "__main__":
    print("=== Testing CategoryManager ===")

    manager = CategoryManager()

    print(f"All categories: {manager.get_all_categories()}")
    print(f"Academic group: {manager.get_category_group('Academic')}")

    # Test validation
    test_cats = ["Geography", "History", "Fake Category"]
    valid_cats = manager.validate_categories(test_cats)
    print(f"Validated categories: {valid_cats}")

    # Test filtering
    include_result = manager.get_filtered_categories("include", ["Geography", "History"])
    print(f"Include mode: {include_result}")

    exclude_result = manager.get_filtered_categories("exclude", ["Geography", "History"])
    print(f"Exclude mode: {exclude_result}")

    print("\nAll tests passed!")