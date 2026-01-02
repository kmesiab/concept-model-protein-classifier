# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/protein-classifier-api"
  retention_in_days = 7
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn

  tags = {
    Name = "protein-classifier-ecs-logs"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "protein-classifier-api-1-0-0-prod-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "protein-classifier-api-1-0-0-prod-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "protein-classifier-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "protein-classifier-api"
      image = "${aws_ecr_repository.api.repository_url}:latest"

      cpu    = var.container_cpu
      memory = var.container_memory

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "PORT"
          value = tostring(var.container_port)
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import sys, urllib.request; resp = urllib.request.urlopen('http://localhost:${var.container_port}${var.health_check_path}'); sys.exit(0 if 200 <= resp.getcode() < 400 else 1)\""]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  tags = {
    Name = "protein-classifier-api-task"
  }
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "protein-classifier-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs.arn
    container_name   = "protein-classifier-api"
    container_port   = var.container_port
  }

  # IMPORTANT: Deployment Circuit Breaker Behavior
  #
  # The circuit breaker is configured to automatically rollback failed deployments.
  # When a rollback occurs, the ECS deployment command completes successfully (exit code 0),
  # which means GitHub Actions will show a green checkmark even though the new version
  # was NOT deployed.
  #
  # This can create confusion where:
  # - GitHub Actions workflow shows SUCCESS
  # - But ECS service is still running the previous task definition
  # - The deployment was automatically rolled back due to health check failures
  #
  # To verify actual deployment status:
  # 1. Check CloudWatch logs for deployment events
  # 2. Verify running task definition matches expected version
  # 3. Monitor ECS service events in AWS Console
  #
  # Consider adding post-deployment verification steps in the GitHub Actions workflow
  # to confirm the desired task definition is actually running.

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role_policy_attachment.ecs_task_execution_role_policy
  ]

  tags = {
    Name = "protein-classifier-api-service"
  }
}
