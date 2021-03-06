from __future__ import unicode_literals

from theory.utils.datastructures import OrderedSet
from theory.db.migrations.state import ProjectState


class MigrationGraph(object):
  """
  Represents the digraph of all migrations in a project.

  Each migration is a node, and each dependency is an edge. There are
  no implicit dependencies between numbered migrations - the numbering is
  merely a convention to aid file listing. Every new numbered migration
  has a declared dependency to the previous number, meaning that VCS
  branch merges can be detected and resolved.

  Migrations files can be marked as replacing another set of migrations -
  this is to support the "squash" feature. The graph handler isn't responsible
  for these; instead, the code to load them in here should examine the
  migration files and if the replaced migrations are all either unapplied
  or not present, it should ignore the replaced ones, load in just the
  replacing migration, and repoint any dependencies that pointed to the
  replaced migrations to point to the replacing one.

  A node should be a tuple: (appPath, migrationName). The tree special-cases
  things within an app - namely, root nodes and leaf nodes ignore dependencies
  to other apps.
  """

  def __init__(self):
    self.nodes = {}
    self.dependencies = {}
    self.dependents = {}

  def addNode(self, node, implementation):
    self.nodes[node] = implementation

  def addDependency(self, child, parent):
    if child not in self.nodes:
      raise KeyError("Dependency references nonexistent child node %r" % (child,))
    if parent not in self.nodes:
      raise KeyError("Dependency references nonexistent parent node %r" % (parent,))
    self.dependencies.setdefault(child, set()).add(parent)
    self.dependents.setdefault(parent, set()).add(child)

  def forwardsPlan(self, node):
    """
    Given a node, returns a list of which previous nodes (dependencies)
    must be applied, ending with the node itself.
    This is the list you would follow if applying the migrations to
    a database.
    """
    if node not in self.nodes:
      raise ValueError("Node %r not a valid node" % (node, ))
    return self.dfs(node, lambda x: self.dependencies.get(x, set()))

  def backwardsPlan(self, node):
    """
    Given a node, returns a list of which dependent nodes (dependencies)
    must be unapplied, ending with the node itself.
    This is the list you would follow if removing the migrations from
    a database.
    """
    if node not in self.nodes:
      raise ValueError("Node %r not a valid node" % (node, ))
    return self.dfs(node, lambda x: self.dependents.get(x, set()))

  def rootNodes(self, app=None):
    """
    Returns all root nodes - that is, nodes with no dependencies inside
    their app. These are the starting point for an app.
    """
    roots = set()
    for node in self.nodes:
      if not any(key[0] == node[0] for key in self.dependencies.get(node, set())) and (not app or app == node[0]):
        roots.add(node)
    return sorted(roots)

  def leafNodes(self, app=None):
    """
    Returns all leaf nodes - that is, nodes with no dependents in their app.
    These are the "most current" version of an app's schema.
    Having more than one per app is technically an error, but one that
    gets handled further up, in the interactive command - it's usually the
    result of a VCS merge and needs some user input.
    """
    leaves = set()
    for node in self.nodes:
      if not any(key[0] == node[0] for key in self.dependents.get(node, set())) and (not app or app == node[0]):
        leaves.add(node)
    return sorted(leaves)

  def dfs(self, start, getChildren):
    """
    Dynamic programming based depth first search, for finding dependencies.
    """
    cache = {}

    def _dfs(start, getChildren, path):
      # If we already computed this, use that (dynamic programming)
      if (start, getChildren) in cache:
        return cache[(start, getChildren)]
      # If we've traversed here before, that's a circular dep
      if start in path:
        raise CircularDependencyError(path[path.index(start):] + [start])
      # Build our own results list, starting with us
      results = []
      results.append(start)
      # We need to add to results all the migrations this one depends on
      children = sorted(getChildren(start))
      path.append(start)
      for n in children:
        results = _dfs(n, getChildren, path) + results
      path.pop()
      # Use OrderedSet to ensure only one instance of each result
      results = list(OrderedSet(results))
      # Populate DP cache
      cache[(start, getChildren)] = results
      # Done!
      return results
    return _dfs(start, getChildren, [])

  def __str__(self):
    return "Graph: %s nodes, %s edges" % (len(self.nodes), sum(len(x) for x in self.dependencies.values()))

  def makeState(self, nodes=None, atEnd=True, realApps=None):
    """
    Given a migration node or nodes, returns a complete ProjectState for it.
    If atEnd is False, returns the state before the migration has run.
    If nodes is not provided, returns the overall most current project state.
    """
    if nodes is None:
      nodes = list(self.leafNodes())
    if len(nodes) == 0:
      return ProjectState()
    if not isinstance(nodes[0], tuple):
      nodes = [nodes]
    plan = []
    for node in nodes:
      for migration in self.forwardsPlan(node):
        if migration not in plan:
          if not atEnd and migration in nodes:
            continue
          plan.append(migration)
    projectState = ProjectState(realApps=realApps)
    for node in plan:
      projectState = self.nodes[node].mutateState(projectState)
    return projectState

  def __contains__(self, node):
    return node in self.nodes


class CircularDependencyError(Exception):
  """
  Raised when there's an impossible-to-resolve circular dependency.
  """
  pass
