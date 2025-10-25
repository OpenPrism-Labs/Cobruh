# Cobruh Implementation Roadmap

> **AUTHORITATIVE SOURCE for development timeline, phases, milestones, and tasks**  
> Follow this roadmap for the complete 12-week development plan.  
> Last Updated: October 25, 2025 | Version: 1.0.0

---

## Phase 1: Foundation (Weeks 1-3)

### Week 1: Core Data Structures

#### Milestone 1.1: Basic Container Implementation
**Goal**: Implement basic configuration containers

**Tasks**:
1. Create `BaseContainer` class
   - Attribute and dict-style access
   - Dot notation support (`config.model.name`)
   - Type annotations and protocols

2. Implement `DictConfig`
   - Nested dictionary wrapper
   - Read-only mode support
   - Metadata tracking
   - `__getitem__`, `__setitem__`, `__contains__`
   - `get()`, `keys()`, `values()`, `items()` methods

3. Implement `ListConfig`
   - List wrapper with type safety
   - Index access and slicing
   - `append()`, `extend()`, `insert()` methods

4. Create `Node` classes
   - `ValueNode`: Stores actual values
   - `MissingNode`: Represents missing mandatory values
   - `InterpolationNode`: Unresolved interpolations

**Deliverables**:
- [ ] `cobruh/config/base_container.py`
- [ ] `cobruh/config/dictconfig.py`
- [ ] `cobruh/config/listconfig.py`
- [ ] `cobruh/config/nodes.py`
- [ ] Unit tests for all containers

**Acceptance Criteria**:
- Can create nested configs from dicts/lists
- Dot notation access works
- Type preservation works
- All tests pass

---

#### Milestone 1.2: Error Handling System
**Goal**: Define all custom exceptions and error handling

**Tasks**:
1. Create exception hierarchy
   - `CobruhException` (base)
   - `ConfigCompositionError`
   - `ConfigAttributeError`
   - `MissingMandatoryValue`
   - `ValidationError`
   - `InterpolationResolutionError`
   - `CircularReferenceError`

2. Implement error context tracking
   - Config path to error location
   - Parent config information
   - Helpful error messages

**Deliverables**:
- [ ] `cobruh/config/errors.py`
- [ ] Error message formatting utilities

---

#### Milestone 1.3: Type System
**Goal**: Implement type validation and conversion

**Tasks**:
1. Create type validators
   - Primitive types (int, str, float, bool)
   - Container types (list, dict)
   - Optional types
   - Union types
   - Custom classes

2. Type conversion utilities
   - String to typed value
   - Type coercion rules

**Deliverables**:
- [ ] `cobruh/validation/type_validator.py`
- [ ] `cobruh/utils/conversion.py`
- [ ] Unit tests for type validation

---

### Week 2: Configuration Loading

#### Milestone 2.1: YAML Loader
**Goal**: Load configurations from YAML files

**Tasks**:
1. Implement safe YAML loading
   - Use `yaml.safe_load()`
   - Custom YAML constructors if needed
   - Error handling for malformed YAML

2. Create config file search system
   - Search path management
   - File discovery in config directories
   - Group-based organization support

3. Implement caching
   - Cache loaded YAML files
   - Invalidation strategy

**Deliverables**:
- [ ] `cobruh/loader/yaml_loader.py`
- [ ] `cobruh/loader/search_path.py`
- [ ] Unit tests with fixture YAML files

**Acceptance Criteria**:
- Can load simple YAML files
- Can discover configs in subdirectories
- Caching works correctly

---

#### Milestone 2.2: Structured Config Support
**Goal**: Support Python dataclasses as configs

**Tasks**:
1. Dataclass introspection
   - Extract fields and types
   - Handle default values
   - Support nested dataclasses

2. Convert dataclass to DictConfig
   - Preserve type information
   - Handle optional fields
   - Support MISSING sentinel

3. Validation against dataclass schema
   - Type checking
   - Required field validation

**Deliverables**:
- [ ] `cobruh/loader/structured_loader.py`
- [ ] `cobruh/types/structured.py`
- [ ] Unit tests with dataclass examples

---

#### Milestone 2.3: Config Store
**Goal**: Implement global configuration registry

**Tasks**:
1. Create singleton ConfigStore
   - Store named configs
   - Support config groups
   - Thread-safe access

2. Registration API
   - `store()` method
   - `get()` method
   - Group-based storage

3. Integration with loaders
   - Load from store
   - Priority: store vs file system

**Deliverables**:
- [ ] `cobruh/core/config_store.py`
- [ ] Unit tests for config store

---

### Week 3: Merging and Composition

#### Milestone 3.1: Configuration Merging
**Goal**: Implement smart config merging

**Tasks**:
1. Define merge strategies
   - Dict-to-dict: recursive merge
   - List-to-list: replace
   - Value-to-value: override
   - None handling
   - MISSING handling

2. Implement merge algorithm
   - Deep merge for nested structures
   - Preserve metadata
   - Type preservation

3. Handle edge cases
   - Type conflicts
   - Circular references
   - Merge order

**Deliverables**:
- [ ] `cobruh/utils/merge.py`
- [ ] Comprehensive unit tests

**Acceptance Criteria**:
- All merge strategies work
- Edge cases handled gracefully
- No data loss during merge

---

#### Milestone 3.2: Defaults List Processing
**Goal**: Process defaults list in configs

**Tasks**:
1. Parse defaults list
   - Support different syntaxes
   - Handle optional defaults
   - Group selection syntax

2. Implement composition order
   - Load defaults in order
   - Merge with base config
   - Apply overrides

3. Handle special keywords
   - `_self_`: position of main config
   - Optional groups
   - Package directives

**Deliverables**:
- [ ] `cobruh/loader/defaults_list.py`
- [ ] Integration tests

---

## Phase 2: Core Features (Weeks 4-6)

### Week 4: Override System

#### Milestone 4.1: Override Parser
**Goal**: Parse command-line overrides

**Tasks**:
1. Implement override syntax parsing
   - `key=value`
   - `key.nested.path=value`
   - `+key=value` (force add)
   - `~key=value` (override or add)
   - `++key=value` (force add to config)
   - `key=null` (delete)

2. Group selection parsing
   - `group=option`
   - `+group=option`
   - `group/subgroup=option`

3. Type inference from strings
   - Auto-detect int, float, bool
   - Keep strings as strings
   - Support explicit type hints

**Deliverables**:
- [ ] `cobruh/overrides/parser.py`
- [ ] `cobruh/overrides/types.py`
- [ ] Comprehensive parser tests

---

#### Milestone 4.2: Override Application
**Goal**: Apply overrides to configurations

**Tasks**:
1. Implement override application
   - Navigate to nested keys
   - Create missing paths
   - Delete keys
   - Validate operations

2. Group override handling
   - Load selected group config
   - Merge into main config
   - Handle conflicts

3. Override validation
   - Check for valid paths
   - Type compatibility
   - Permission checks (read-only)

**Deliverables**:
- [ ] `cobruh/overrides/applier.py`
- [ ] Integration tests

---

### Week 5: Interpolation System

#### Milestone 5.1: Interpolation Resolution
**Goal**: Resolve variable references

**Tasks**:
1. Detect interpolations
   - Regex pattern matching
   - Extract variable paths
   - Parse resolver syntax

2. Implement resolution engine
   - Recursive resolution
   - Lazy evaluation
   - Caching resolved values

3. Circular reference detection
   - Build dependency graph
   - Detect cycles
   - Provide clear error messages

**Deliverables**:
- [ ] `cobruh/resolver/interpolation.py`
- [ ] `cobruh/resolver/graph.py`
- [ ] Unit tests for resolution

**Acceptance Criteria**:
- Simple refs work: `${key}`
- Nested refs work: `${a.b.c}`
- Circular refs detected
- Performance acceptable

---

#### Milestone 5.2: Built-in Resolvers
**Goal**: Implement standard resolvers

**Tasks**:
1. Environment variable resolver
   - `${env:VAR}`
   - `${oc.env:VAR,default}`
   - Error on missing vars

2. OmegaConf resolvers
   - `${oc.decode:value}`: URL decode
   - `${oc.env:VAR}`: Environment variables
   - `${oc.deprecated:...}`: Deprecation warnings

3. Utility resolvers
   - `${now:%Y-%m-%d}`: Current timestamp
   - `${uuid:}`: Generate UUID
   - Custom user resolvers

**Deliverables**:
- [ ] `cobruh/resolver/resolvers.py`
- [ ] `cobruh/resolver/custom.py`
- [ ] Tests for all resolvers

---

### Week 6: Main Decorator and Composition

#### Milestone 6.1: Composition Engine
**Goal**: Orchestrate config composition

**Tasks**:
1. Implement `Composer` class
   - Load primary config
   - Process defaults list
   - Merge all configs
   - Apply overrides
   - Resolve interpolations
   - Validate final config

2. Composition pipeline
   - Clear step ordering
   - Error handling at each step
   - Logging/debugging support

3. Caching and optimization
   - Cache loaded configs
   - Minimize redundant operations
   - Lazy resolution where possible

**Deliverables**:
- [ ] `cobruh/core/composer.py`
- [ ] Integration tests

**Acceptance Criteria**:
- Can compose complex configs
- Overrides work correctly
- Performance is acceptable
- Errors are informative

---

#### Milestone 6.2: Main Decorator
**Goal**: Implement `@cobruh.main()` decorator

**Tasks**:
1. Create decorator function
   - Accept config_path, config_name
   - Parse command-line args
   - Call composer
   - Pass config to user function

2. Output directory management
   - Create unique output dir
   - Store config snapshot
   - Setup logging

3. Global context management
   - Store current job info
   - Provide access to runtime info

**Deliverables**:
- [ ] `cobruh/core/decorator.py`
- [ ] `cobruh/core/global_context.py`
- [ ] End-to-end tests

---

## Phase 3: Advanced Features (Weeks 7-9)

### Week 7: Utilities and Helpers

#### Milestone 7.1: Instantiate Utility
**Goal**: Implement `cobruh.utils.instantiate()`

**Tasks**:
1. Parse `_target_` field
   - Import module and class
   - Handle partial paths
   - Error on missing targets

2. Instantiate objects
   - Pass config as kwargs
   - Support positional args
   - Handle nested instantiation
   - Support `_partial_` for functools.partial

3. Special field handling
   - `_recursive_`: recursive instantiation
   - `_convert_`: type conversion
   - Reserved keys handling

**Deliverables**:
- [ ] `cobruh/utils/instantiate.py`
- [ ] Unit tests with various classes

**Acceptance Criteria**:
- Can instantiate simple classes
- Nested instantiation works
- Partial instantiation works
- Clear errors on failures

---

#### Milestone 7.2: Path Utilities
**Goal**: Helper functions for config manipulation

**Tasks**:
1. Path manipulation
   - Parse dotted paths
   - Navigate nested configs
   - Set values at paths
   - Delete at paths

2. Config utilities
   - Deep copy configs
   - Config to dict conversion
   - Pretty printing
   - Diff two configs

**Deliverables**:
- [ ] `cobruh/utils/path_utils.py`
- [ ] Unit tests

---

### Week 8: Multirun and Sweeps

#### Milestone 8.1: Multirun Support
**Goal**: Enable parameter sweeps

**Tasks**:
1. Multirun mode detection
   - `-m` or `--multirun` flag
   - Parse sweep specifications

2. Sweep parameter parsing
   - Comma-separated values: `lr=0.1,0.01`
   - Range syntax: `batch_size=range(16,128,16)`
   - Glob patterns for groups

3. Job launcher
   - Generate all combinations
   - Execute jobs sequentially/parallel
   - Collect results
   - Handle failures

**Deliverables**:
- [ ] `cobruh/cli/multirun.py`
- [ ] Integration tests

---

#### Milestone 8.2: Job Management
**Goal**: Manage multiple job runs

**Tasks**:
1. Job tracking
   - Unique job IDs
   - Job status tracking
   - Output organization

2. Parallel execution
   - Thread/process pools
   - Resource management
   - Cancellation support

**Deliverables**:
- [ ] Job management utilities
- [ ] Tests for parallel execution

---

### Week 9: Plugin System and Polish

#### Milestone 9.1: Plugin System
**Goal**: Enable extensibility

**Tasks**:
1. Plugin interface
   - Base plugin class
   - Lifecycle hooks
   - Registration API

2. Plugin discovery
   - Entry points
   - Manual registration
   - Plugin configuration

3. Built-in plugins
   - Shell completion
   - Help generation
   - Config validation

**Deliverables**:
- [ ] `cobruh/plugins/base.py`
- [ ] `cobruh/plugins/manager.py`
- [ ] Built-in plugins
- [ ] Plugin tests

---

#### Milestone 9.2: CLI Enhancements
**Goal**: Improve command-line experience

**Tasks**:
1. Help system
   - Auto-generate help text
   - Show available groups
   - Example commands

2. Tab completion
   - Bash completion
   - Zsh completion
   - Fish completion

3. Validation and warnings
   - Unused overrides detection
   - Deprecation warnings
   - Best practice hints

**Deliverables**:
- [ ] Enhanced CLI
- [ ] Completion scripts
- [ ] User documentation

---

## Phase 4: Testing and Documentation (Weeks 10-12)

### Week 10: Comprehensive Testing

#### Milestone 10.1: Test Coverage
**Goal**: Achieve >90% test coverage

**Tasks**:
1. Unit test completion
   - Cover all modules
   - Edge cases
   - Error paths

2. Integration tests
   - End-to-end workflows
   - Real-world scenarios
   - Performance tests

3. Regression tests
   - Known issues
   - Bug fixes
   - Breaking changes

**Deliverables**:
- [ ] Complete test suite
- [ ] Coverage report
- [ ] CI/CD integration

---

#### Milestone 10.2: Performance Optimization
**Goal**: Ensure acceptable performance

**Tasks**:
1. Benchmarking
   - Composition speed
   - Interpolation resolution
   - Merge operations
   - Memory usage

2. Optimization
   - Profile hot paths
   - Reduce allocations
   - Caching strategies

3. Scalability testing
   - Large configs
   - Deep nesting
   - Many overrides

**Deliverables**:
- [ ] Benchmark suite
- [ ] Performance report
- [ ] Optimization PRs

---

### Week 11: Documentation

#### Milestone 11.1: User Documentation
**Goal**: Complete user-facing docs

**Tasks**:
1. Getting started guide
   - Installation
   - Quick start
   - Basic examples

2. Tutorials
   - Step-by-step guides
   - Common patterns
   - Best practices

3. API reference
   - Auto-generated docs
   - Examples for each API
   - Type signatures

**Deliverables**:
- [ ] Documentation website
- [ ] Tutorial notebooks
- [ ] API reference

---

#### Milestone 11.2: Developer Documentation
**Goal**: Help contributors

**Tasks**:
1. Architecture docs
   - Design decisions
   - Component interactions
   - Extension points

2. Contributing guide
   - Setup instructions
   - Code style
   - PR process

3. Internals documentation
   - Implementation details
   - Algorithms
   - Performance considerations

**Deliverables**:
- [ ] CONTRIBUTING.md
- [ ] ARCHITECTURE.md (enhance)
- [ ] Developer guide

---

### Week 12: Release Preparation

#### Milestone 12.1: Release Engineering
**Goal**: Prepare for initial release

**Tasks**:
1. Packaging
   - Setup `pyproject.toml`
   - Build scripts
   - Wheel generation
   - Source distribution

2. CI/CD pipeline
   - Automated testing
   - Automated releases
   - Version bumping

3. Release checklist
   - Changelog
   - Migration guide
   - Announcement
   - PyPI upload

**Deliverables**:
- [ ] Published package on PyPI
- [ ] GitHub releases
- [ ] Release announcement

---

#### Milestone 12.2: Community and Support
**Goal**: Enable community growth

**Tasks**:
1. Community setup
   - GitHub issues templates
   - Discussion forums
   - Contributing guidelines

2. Examples and templates
   - Project templates
   - Real-world examples
   - Integration examples

3. Marketing
   - Blog post
   - Social media
   - Documentation site

**Deliverables**:
- [ ] Community resources
- [ ] Example repository
- [ ] Launch announcement

---

## Success Metrics

### Technical Metrics
- [ ] >90% test coverage
- [ ] All core features implemented
- [ ] Performance benchmarks met:
  - Config composition: <100ms for typical configs
  - Memory overhead: <10MB for typical usage
  - Supports configs with >1000 keys
- [ ] Zero critical bugs

### Documentation Metrics
- [ ] 100% API documentation coverage
- [ ] At least 10 tutorials/examples
- [ ] Getting started guide complete
- [ ] Architecture documentation complete

### Community Metrics
- [ ] Published on PyPI
- [ ] GitHub stars >100
- [ ] Active contributors >3
- [ ] Issues response time <48h

---

## Risk Mitigation

### Technical Risks
1. **Complexity of interpolation resolution**
   - Mitigation: Start simple, iterate
   - Fallback: Limit interpolation depth

2. **Performance with large configs**
   - Mitigation: Early benchmarking
   - Fallback: Optimization phase

3. **YAML edge cases**
   - Mitigation: Comprehensive testing
   - Fallback: Document limitations

### Project Risks
1. **Scope creep**
   - Mitigation: Strict milestone focus
   - Defer nice-to-have features

2. **Timeline delays**
   - Mitigation: Weekly checkpoints
   - Buffer time in schedule

3. **Breaking changes from Hydra updates**
   - Mitigation: Version compatibility matrix
   - Clear migration guides

---

## Post-Launch Roadmap

### Version 1.1 (Q1 after launch)
- [ ] Advanced plugins
- [ ] Remote config loading
- [ ] Config schema generation
- [ ] Interactive config explorer

### Version 1.2 (Q2 after launch)
- [ ] Distributed sweeps
- [ ] Cloud integration
- [ ] Config validation DSL
- [ ] Performance optimizations

### Version 2.0 (Future)
- [ ] Breaking changes if needed
- [ ] Major architecture improvements
- [ ] Extended plugin ecosystem
