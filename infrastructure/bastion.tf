# ─── SSH Key Pair ─────────────────────────────────────────────
# Upload your public key to AWS so the bastion trusts your laptop

resource "aws_key_pair" "bastion" {
  key_name   = "${var.project_name}-bastion-${var.environment}"
  public_key = file("C:/Users/tomuh/Desktop/terraform/.ssh/car-assistant-bastion.pub")
}

# ─── Bastion Security Group ───────────────────────────────────
# Only allows SSH from your IP — nothing else

resource "aws_security_group" "bastion" {
  name        = "${var.project_name}-bastion-${var.environment}"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH from developer laptop only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.developer_ip]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── Bastion EC2 Instance ─────────────────────────────────────
# t4g.nano — cheapest ARM instance, costs ~$3/month always on
# Stop it when not working and it costs almost nothing

resource "aws_instance" "bastion" {
  ami = "ami-0d3afa848fc8b043e"  # Amazon Linux 2023 ARM64 eu-central-1
  instance_type          = "t4g.nano"
  subnet_id              = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.bastion.id]
  key_name               = aws_key_pair.bastion.key_name

  # Give it a public IP so your laptop can reach it
  associate_public_ip_address = true

  root_block_device {
    volume_size = 8     # minimum disk size — 8GB is plenty
    volume_type = "gp3"
  }
}

# Elastic IP — fixed public IP that persists across stop/start
resource "aws_eip" "bastion" {
  instance   = aws_instance.bastion.id
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]
}