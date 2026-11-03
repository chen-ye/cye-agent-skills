# GitHub GraphQL API Reference for PR Review Threads

This reference covers the GitHub GraphQL queries and mutations used by a reviewer to inspect, verify, and resolve review threads.

## Authentication & Multi-Host Configuration

When working with GitHub Enterprise Server or custom GitHub hosts:
1. Always pass `--hostname <domain>` to `gh api`. By default, `gh api` targets `api.github.com`.
2. To verify authentication for an enterprise host:
   ```bash
   gh auth status --hostname github.example.com
   ```
3. Token scopes must include `repo` and `read:org`.

## GraphQL Queries

### Fetch PR Review Threads with Details
```graphql
query(
  $owner: String!,
  $repo: String!,
  $number: Int!,
  $threadsCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      url
      title
      state
      author { login }
      headRefName
      baseRefName

      reviewThreads(first: 100, after: $threadsCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          originalLine
          diffSide
          startLine
          resolvedBy { login }
          comments(first: 100) {
            nodes {
              id
              body
              diffHunk
              createdAt
              updatedAt
              author { login }
            }
          }
        }
      }
    }
  }
}
```

## Resolution Authority & Audit Fields

Each `PullRequestReviewThread` node exposes:
- `comments.nodes[0].author.login`: The **original commenter** who opened the review thread.
- `resolvedBy.login`: The user who marked the thread as resolved (present when `isResolved` is `true`).
- `pullRequest.author.login`: The PR author / implementer.

`fetch_unresolved_comments.py` computes and attaches the following fields to every thread object in JSON mode (and surfaces them in summary mode):
- `originalCommenter`: `comments.nodes[0].author.login`
- `resolvedByLogin`: `resolvedBy.login`
- `isResolvedByOriginalCommenter`: `true` only when `isResolved` is `true` and `resolvedBy.login` matches `originalCommenter` (case-insensitive).
- `isResolvedByOther`: `true` when `isResolved` is `true` and `isResolvedByOriginalCommenter` is `false` (e.g., resolved by the PR author or a third party rather than the reviewer who opened the thread).
- `isResolvedByPrAuthor`: `true` when `isResolved` is `true` and `resolvedBy.login` matches `pullRequest.author.login`.

## GraphQL Mutations

### Resolve Review Thread
```graphql
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread {
      id
      isResolved
      resolvedBy {
        login
      }
    }
  }
}
```

### Unresolve Review Thread
```graphql
mutation($threadId: ID!) {
  unresolveReviewThread(input: { threadId: $threadId }) {
    thread {
      id
      isResolved
    }
  }
}
```
